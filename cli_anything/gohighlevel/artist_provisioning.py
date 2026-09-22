"""Bounded Tattoo.co setup receipts. Never used by the booking worker.

SQLite commits the uncertain-create marker before network I/O. A restart or a
second process can reconcile, but cannot repeat an attempted create.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MASTER_LOCATION = "Vh2R6tYeFcaMOFKKSw4a"
STAGES = ["New inquiry", "Contacted", "Qualified", "Consultation/quote", "Booked"]


class SetupError(ValueError):
    """Safe operator-facing error; never includes provider response bodies."""


def plan_artist(artist_id: int, artist_name: str) -> dict:
    if type(artist_id) is not int or artist_id <= 0:
        raise SetupError("Artist ID must be a positive integer")
    if not isinstance(artist_name, str) or not artist_name.strip() or len(artist_name) > 120:
        raise SetupError("Artist name must contain 1-120 characters")
    if any(ord(c) < 32 for c in artist_name) or re.search(r"[\[\]]", artist_name):
        raise SetupError("Artist name cannot contain control characters or brackets")
    return {"version": 1, "locationId": MASTER_LOCATION, "artistId": artist_id,
            "pipelineName": f"Tattoo.co — {artist_name.strip()} [{artist_id}]",
            "tagName": f"tattoo_artist_{artist_id}", "stages": list(STAGES)}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReceiptStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Receipts contain only configuration, safe IDs, timestamps and error codes.
        if not self.path.exists():
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
            except FileExistsError:
                pass
        self.db = sqlite3.connect(self.path, timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
          CREATE TABLE IF NOT EXISTS artist_setup (
            location TEXT NOT NULL, artist INTEGER NOT NULL, plan TEXT NOT NULL,
            proof TEXT, PRIMARY KEY(location, artist));
          CREATE TABLE IF NOT EXISTS setup_operations (
            location TEXT NOT NULL, artist INTEGER NOT NULL, kind TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'planned', remote_id TEXT,
            receipt TEXT, attempted_at TEXT, confirmed_at TEXT, error TEXT,
            PRIMARY KEY(location, artist, kind));
        """)

    def close(self):
        self.db.close()

    def prepare(self, plan: dict, proof: str | None):
        key = (plan["locationId"], plan["artistId"])
        encoded = json.dumps(plan, sort_keys=True)
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO artist_setup VALUES (?, ?, ?, ?)", (*key, encoded, proof))
            row = self.db.execute("SELECT plan FROM artist_setup WHERE location=? AND artist=?", key).fetchone()
            if row["plan"] != encoded:
                raise SetupError("Stored plan differs; preserve the receipt and review the existing mapping")
            if proof:
                self.db.execute("UPDATE artist_setup SET proof=? WHERE location=? AND artist=?", (proof, *key))
            for kind in ("pipeline", "tag"):
                self.db.execute("INSERT OR IGNORE INTO setup_operations(location,artist,kind) VALUES (?,?,?)", (*key, kind))

    def get(self, plan, kind):
        return dict(self.db.execute("SELECT * FROM setup_operations WHERE location=? AND artist=? AND kind=?",
                                   (plan["locationId"], plan["artistId"], kind)).fetchone())

    def claim(self, plan, kind) -> bool:
        with self.db:
            result = self.db.execute("""UPDATE setup_operations SET state='creating',attempted_at=?,error=NULL
              WHERE location=? AND artist=? AND kind=? AND state='planned' AND remote_id IS NULL""",
              (now(), plan["locationId"], plan["artistId"], kind))
        return result.rowcount == 1

    def error(self, plan, kind, code):
        with self.db:
            self.db.execute("UPDATE setup_operations SET error=? WHERE location=? AND artist=? AND kind=?",
                            (code, plan["locationId"], plan["artistId"], kind))

    def save_id(self, plan, kind, remote_id):
        with self.db:
            row = self.get(plan, kind)
            if row["remote_id"] and row["remote_id"] != remote_id:
                raise SetupError("Persisted remote ID conflicts with provider result")
            self.db.execute("UPDATE setup_operations SET remote_id=? WHERE location=? AND artist=? AND kind=?",
                            (remote_id, plan["locationId"], plan["artistId"], kind))

    def confirm(self, plan, kind, receipt):
        with self.db:
            self.save_id(plan, kind, receipt["id"])
            self.db.execute("""UPDATE setup_operations SET state='confirmed', receipt=?,confirmed_at=?,error=NULL
              WHERE location=? AND artist=? AND kind=?""",
              (json.dumps(receipt), now(), plan["locationId"], plan["artistId"], kind))

    def result(self, plan, status):
        operations = {}
        for kind in ("pipeline", "tag"):
            row = self.get(plan, kind)
            operations[kind] = {k: row[k] for k in ("state", "remote_id", "attempted_at", "confirmed_at", "error")}
            operations[kind]["receipt"] = json.loads(row["receipt"]) if row["receipt"] else None
        return {"status": status, "plan": plan, "operations": operations,
                "activation": "not_performed"}


def rows_from(body, key):
    if not isinstance(body, dict) or not isinstance(body.get(key), list):
        raise SetupError("Provider list response is malformed; no create is safe")
    if any(not isinstance(row, dict) for row in body[key]):
        raise SetupError("Provider list contains malformed records")
    # Never interpret a visibly partial list as proof of absence.
    if body.get("nextPage") or body.get("nextPageUrl") or body.get("hasMore"):
        raise SetupError("Provider list is incomplete; manual review required")
    return body[key]


def verified_receipt(row, plan, kind):
    expected = plan["pipelineName" if kind == "pipeline" else "tagName"]
    if not isinstance(row.get("id"), str) or not row["id"] or row.get("name") != expected:
        raise SetupError("Provider record does not match the exact planned identity")
    if row.get("locationId") != plan["locationId"]:
        raise SetupError("Provider record location does not match the master")
    receipt = {"id": row["id"], "name": row["name"], "locationId": row["locationId"]}
    if kind == "pipeline":
        stages = row.get("stages")
        if not isinstance(stages, list) or len(stages) != len(plan["stages"]):
            raise SetupError("Existing pipeline stages need review; no replacement is performed")
        if any(not isinstance(s, dict) or not isinstance(s.get("id"), str) or not s["id"] for s in stages):
            raise SetupError("Pipeline stage IDs are missing")
        # Provider order is used only to verify the approved stage sequence.
        if [s.get("name") for s in stages] != plan["stages"] or len({s["id"] for s in stages}) != len(stages):
            raise SetupError("Pipeline stage identity or order differs from the approved plan")
        receipt["stages"] = [{"id": s["id"], "name": s["name"]} for s in stages]
        receipt["initialStageId"] = stages[0]["id"]
    return receipt


def inspect(client, plan, kind, operation):
    body = client.pipelines.list() if kind == "pipeline" else client.request(
        "GET", "/locations/{locationId}/tags", version="v3")
    rows = rows_from(body, "pipelines" if kind == "pipeline" else "tags")
    name = plan["pipelineName" if kind == "pipeline" else "tagName"]
    matches = [row for row in rows if str(row.get("name", "")).casefold() == name.casefold()]
    remote_id = operation["remote_id"]
    if remote_id:
        exact = [row for row in rows if row.get("id") == remote_id]
        if len(exact) != 1 or len(matches) != 1 or matches[0].get("id") != remote_id:
            raise SetupError("Persisted provider identity is missing or conflicting; never recreate it")
        return verified_receipt(exact[0], plan, kind)
    if len(matches) > 1:
        raise SetupError("Multiple exact-name candidates require review")
    return verified_receipt(matches[0], plan, kind) if matches else None


def run_setup(client, store, plan, *, apply=False, confirm_location=None, proof=None):
    if not isinstance(plan, dict) or plan.get("version") != 1:
        raise SetupError("Unsupported provisioning plan")
    artist_id = plan.get("artistId")
    name = plan.get("pipelineName", "")
    prefix, suffix = "Tattoo.co — ", f" [{artist_id}]"
    if not isinstance(name, str) or not name.startswith(prefix) or not name.endswith(suffix):
        raise SetupError("Plan must use the canonical artist identity")
    if plan != plan_artist(artist_id, name[len(prefix):-len(suffix)]):
        raise SetupError("Plan differs from the supported artist setup contract")
    if client.require_location_id() != plan["locationId"] or plan["locationId"] != MASTER_LOCATION:
        raise SetupError("Client and plan must target the Tattoo.co master location")
    if apply and (confirm_location != MASTER_LOCATION or not proof or not proof.strip()
                  or os.environ.get("TAT100_GHL_ROLLOUT_ENABLED") != "true"):
        raise SetupError("Apply requires confirmed master location, reviewed proof reference, and rollout gate")
    store.prepare(plan, proof if apply else None)
    created = False
    for kind in ("pipeline", "tag"):
        operation = store.get(plan, kind)
        try:
            receipt = inspect(client, plan, kind, operation)
        except Exception:
            store.error(plan, kind, "provider_read_or_identity_review")
            return store.result(plan, "needs_review")
        if receipt:
            store.confirm(plan, kind, receipt)
            continue
        if operation["state"] != "planned":
            store.error(plan, kind, "uncertain_create_not_found")
            return store.result(plan, "needs_reconciliation")
        if not apply or created:
            return store.result(plan, "ready_for_apply" if not created else "resume_required")
        if not store.claim(plan, kind):
            return store.result(plan, "concurrent_operation")
        created = True
        try:
            body = (client.pipelines.create(name=plan["pipelineName"], stages=plan["stages"])
                    if kind == "pipeline" else client.request(
                        "POST", "/locations/{locationId}/tags", body={"name": plan["tagName"]}, version="v3"))
            row = body.get("pipeline", body) if kind == "pipeline" and isinstance(body, dict) else body.get("tag")
            if not isinstance(row, dict) or not isinstance(row.get("id"), str) or not row["id"]:
                raise SetupError("Create result lacks a persisted ID")
            # Persist any returned ID before readback, even when its fields are wrong.
            store.save_id(plan, kind, row["id"])
            receipt = inspect(client, plan, kind, store.get(plan, kind))
            if not receipt:
                raise SetupError("Created object not yet visible")
            store.confirm(plan, kind, receipt)
        except Exception:
            store.error(plan, kind, "create_outcome_requires_reconciliation")
            return store.result(plan, "needs_reconciliation")
    return store.result(plan, "verified_for_admin_binding")
