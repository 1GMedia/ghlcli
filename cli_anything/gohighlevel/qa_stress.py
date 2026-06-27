"""Reusable stress-test harness for ghlcli."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from cli_anything.gohighlevel.coverage import build_endpoint_coverage


PIT_RE = re.compile(r"pit-[A-Za-z0-9-]{12,}")
SECRET_ENV_NAMES = (
    "GHL_TEST_SUBACCOUNT_PIT",
    "GHL_TEST_AGENCY_PIT",
    "GHL_API_KEY",
    "GHL_FIREBASE_TOKEN",
    "GHL_FIREBASE_REFRESH_TOKEN",
)


@dataclass
class StressResult:
    name: str
    mode: str
    status: str
    command: list[str]
    exit_code: int | None = None
    duration_ms: int | None = None
    stdout: str = ""
    stderr: str = ""
    note: str = ""


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def redact(value: Any, env: dict[str, str] | None = None) -> Any:
    """Redact PITs and known secret env values from strings or JSON-like data."""
    if isinstance(value, dict):
        return {key: redact(item, env) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item, env) for item in value]
    if not isinstance(value, str):
        return value

    text = PIT_RE.sub("pit-[redacted]", value)
    candidates: list[str] = []
    source_env = env or os.environ
    for name in SECRET_ENV_NAMES:
        token = source_env.get(name, "").strip()
        if token:
            candidates.append(token)
    for token in sorted(candidates, key=len, reverse=True):
        text = text.replace(token, "pit-[redacted]" if token.startswith("pit-") else "[redacted]")
    return text


def _base_env(mode: str) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("PYTHONUNBUFFERED", "1")
    if mode in {"mock", "dry-run"}:
        env.pop("GHL_API_KEY", None)
        env.pop("GHL_LOCATION_ID", None)
    elif mode in {"live-read", "live-write"}:
        subaccount_pit = env.get("GHL_TEST_SUBACCOUNT_PIT", "").strip()
        location_id = env.get("GHL_TEST_LOCATION_ID", "").strip()
        if not subaccount_pit or not location_id:
            raise ValueError(
                "live modes require GHL_TEST_SUBACCOUNT_PIT and GHL_TEST_LOCATION_ID; "
                "tokens must be supplied through ephemeral environment variables"
            )
        env["GHL_API_KEY"] = subaccount_pit
        env["GHL_LOCATION_ID"] = location_id
    return env


def _run_cli(
    args: list[str],
    mode: str,
    env: dict[str, str],
    name: str,
    timeout: int,
    ok_codes: set[int] | None = None,
) -> StressResult:
    command = [sys.executable, "-m", "cli_anything.gohighlevel", *args]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=repo_root(),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        ok = completed.returncode in (ok_codes or {0})
        return StressResult(
            name=name,
            mode=mode,
            status="passed" if ok else "failed",
            command=args,
            exit_code=completed.returncode,
            duration_ms=duration_ms,
            stdout=redact(completed.stdout.strip(), env),
            stderr=redact(completed.stderr.strip(), env),
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - started) * 1000)
        return StressResult(
            name=name,
            mode=mode,
            status="failed",
            command=args,
            exit_code=None,
            duration_ms=duration_ms,
            stdout=redact((exc.stdout or "").strip(), env),
            stderr=redact((exc.stderr or "").strip(), env),
            note=f"Timed out after {timeout}s",
        )


def _json_from_result(result: StressResult) -> Any:
    if not result.stdout:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def _find_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("id", "_id", "contactId", "opportunityId"):
            item = value.get(key)
            if isinstance(item, str) and item:
                return item
        for key in ("contact", "opportunity", "data"):
            found = _find_id(value.get(key))
            if found:
                return found
        for item in value.values():
            found = _find_id(item)
            if found:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _find_id(item)
            if found:
                return found
    return None


def _append_skipped(results: list[StressResult], mode: str, name: str, note: str) -> None:
    results.append(StressResult(name=name, mode=mode, status="skipped", command=[], note=note))


def _help_matrix() -> list[tuple[str, list[str]]]:
    groups = [
        "calendars",
        "capabilities",
        "contacts",
        "conversations",
        "documents",
        "emails",
        "endpoints",
        "forms",
        "locations",
        "internal",
        "mcp",
        "oauth",
        "opportunities",
        "payments",
        "social",
        "workflows",
    ]
    return [("top help", ["--help"])] + [(f"{group} help", [group, "--help"]) for group in groups]


def _dry_run_matrix(output_file: Path) -> list[tuple[str, list[str]]]:
    return [
        ("doctor json", ["--json", "doctor"]),
        ("capabilities merged json", ["--json", "capabilities", "list", "--merged"]),
        ("endpoints list json", ["--json", "endpoints", "list"]),
        ("endpoints show contacts json", ["--json", "endpoints", "show", "contacts"]),
        ("endpoints search contacts json", ["--json", "endpoints", "search", "contacts"]),
        ("mcp servers json", ["--json", "mcp", "servers", "list"]),
        ("mcp tools json", ["--json", "mcp", "tools", "list"]),
        (
            "generic request dry-run",
            ["--json", "request", "GET", "/contacts/", "--param", "locationId=test-location", "--dry-run"],
        ),
        (
            "internal request dry-run",
            [
                "--experimental",
                "--json",
                "internal",
                "request",
                "GET",
                "/workflow/{locationId}",
                "--path-param",
                "locationId=test-location",
                "--dry-run",
            ],
        ),
        (
            "workflow create-step dry local",
            [
                "--experimental",
                "--json",
                "workflows",
                "create-step",
                "--type",
                "wait",
                "--name",
                "qa wait",
                "--value",
                "5",
                "--unit",
                "minutes",
                "--output-file",
                str(output_file),
            ],
        ),
    ]


def _live_read_matrix() -> list[tuple[str, list[str]]]:
    return [
        ("locations get", ["--json", "locations", "get"]),
        ("contacts list", ["--json", "contacts", "list", "--limit", "5"]),
        ("contacts search", ["--json", "contacts", "search", "ghlcli-test", "--limit", "5"]),
        ("opportunities list", ["--json", "opportunities", "list", "--limit", "5"]),
        ("opportunities pipelines", ["--json", "opportunities", "pipelines"]),
        ("calendars list", ["--json", "calendars", "list"]),
        ("calendars groups", ["--json", "calendars", "groups"]),
        ("workflows list", ["--json", "workflows", "list"]),
        ("conversations list", ["--json", "conversations", "list", "--limit", "5"]),
        ("forms list", ["--json", "forms", "list", "--limit", "5"]),
        ("payments transactions", ["--json", "payments", "transactions", "--limit", "5"]),
        ("payments orders", ["--json", "payments", "orders", "--limit", "5"]),
        ("payments invoices", ["--json", "payments", "invoices", "--limit", "5"]),
        ("social accounts", ["--json", "social", "accounts"]),
        ("social posts", ["--json", "social", "posts", "--limit", "5"]),
    ]


def _agency_matrix(env: dict[str, str]) -> list[tuple[str, list[str]]]:
    company_id = env.get("GHL_TEST_COMPANY_ID", "").strip()
    if not env.get("GHL_TEST_AGENCY_PIT", "").strip() or not company_id:
        return []
    return [
        (
            "agency locations search",
            ["--json", "locations", "search", "--company-id", company_id, "--limit", "5"],
        )
    ]


def _extract_first_pipeline_stage(data: Any) -> tuple[str | None, str | None]:
    pipelines = []
    if isinstance(data, dict):
        pipelines = data.get("pipelines") or data.get("data") or data.get("items") or []
    elif isinstance(data, list):
        pipelines = data
    if not isinstance(pipelines, list):
        return None, None
    for pipeline in pipelines:
        if not isinstance(pipeline, dict):
            continue
        pipeline_id = pipeline.get("id") or pipeline.get("_id")
        stages = pipeline.get("stages") or pipeline.get("stagesInfo") or []
        if pipeline_id and isinstance(stages, list) and stages:
            first_stage = stages[0]
            if isinstance(first_stage, dict):
                stage_id = first_stage.get("id") or first_stage.get("_id")
                if stage_id:
                    return pipeline_id, stage_id
    return None, None


def _run_live_writes(results: list[StressResult], env: dict[str, str], timeout: int, prefix: str) -> None:
    email = f"{prefix}@example.invalid"
    contact = _run_cli(
        [
            "--json",
            "contacts",
            "create",
            "--email",
            email,
            "--first-name",
            "Ghlcli",
            "--last-name",
            "Stress",
            "--source",
            prefix,
        ],
        "live-write",
        env,
        "contact create disposable",
        timeout,
    )
    results.append(contact)
    contact_id = _find_id(_json_from_result(contact))
    if not contact_id:
        _append_skipped(results, "live-write", "contact follow-up cleanup", "contact create did not return an id")
        return

    tag = prefix
    contact_steps = [
        ("contact get", ["--json", "contacts", "get", contact_id]),
        ("contact update", ["--json", "contacts", "update", contact_id, "--first-name", "GhlcliUpdated"]),
        ("contact add tag", ["--json", "contacts", "add-tag", contact_id, tag]),
        ("contact remove tag", ["--json", "contacts", "remove-tag", contact_id, tag]),
    ]
    for name, args in contact_steps:
        results.append(_run_cli(args, "live-write", env, name, timeout))

    pipelines_result = _run_cli(
        ["--json", "opportunities", "pipelines"],
        "live-write",
        env,
        "opportunity prerequisite pipelines",
        timeout,
    )
    results.append(pipelines_result)
    pipeline_id, stage_id = _extract_first_pipeline_stage(_json_from_result(pipelines_result))
    opportunity_id = None
    if pipeline_id and stage_id:
        opp_create = _run_cli(
            [
                "--json",
                "opportunities",
                "create",
                "--pipeline-id",
                pipeline_id,
                "--stage-id",
                stage_id,
                "--name",
                prefix,
                "--contact-id",
                contact_id,
                "--value",
                "1",
            ],
            "live-write",
            env,
            "opportunity create disposable",
            timeout,
        )
        results.append(opp_create)
        opportunity_id = _find_id(_json_from_result(opp_create))
        if opportunity_id:
            for name, args in [
                ("opportunity get", ["--json", "opportunities", "get", opportunity_id]),
                ("opportunity update", ["--json", "opportunities", "update", opportunity_id, "--name", f"{prefix}-updated"]),
                ("opportunity delete", ["--json", "opportunities", "delete", opportunity_id]),
            ]:
                results.append(_run_cli(args, "live-write", env, name, timeout))
        else:
            _append_skipped(results, "live-write", "opportunity cleanup", "opportunity create did not return an id")
    else:
        _append_skipped(results, "live-write", "opportunity disposable write", "no pipeline/stage discovered")

    delete_contact = _run_cli(["--json", "contacts", "delete", contact_id], "live-write", env, "contact delete cleanup", timeout)
    results.append(delete_contact)


def _report_path(report_dir: Path, mode: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    if mode.startswith("live"):
        return report_dir / f"qa-report-ghlcli-live-{now.date().isoformat()}.md"
    return report_dir / f"qa-report-ghlcli-{mode}-{now.strftime('%Y%m%dT%H%M%SZ')}.md"


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        f"# ghlcli QA Stress Report ({payload['mode']})",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- ok: `{payload['ok']}`",
        f"- report_mode: `{payload['mode']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Command Matrix", ""])
    lines.append("| status | name | exit | ms | note |")
    lines.append("| --- | --- | ---: | ---: | --- |")
    for item in payload["results"]:
        lines.append(
            f"| {item['status']} | {item['name']} | {item.get('exit_code')} | "
            f"{item.get('duration_ms')} | {item.get('note', '')} |"
        )
    lines.extend(["", "## Coverage Delta", ""])
    coverage_summary = payload.get("coverage", {}).get("summary", {})
    for key, value in coverage_summary.items():
        lines.append(f"- {key}: `{value}`")
    path.write_text("\n".join(lines) + "\n")


def run_stress(
    mode: str = "dry-run",
    report_dir: str | Path = ".gstack/qa-reports",
    timeout: int = 30,
    include_agency: bool = False,
    cli: Any | None = None,
) -> dict[str, Any]:
    if mode not in {"mock", "dry-run", "live-read", "live-write"}:
        raise ValueError(f"Unknown stress mode: {mode}")
    if mode == "live-write" and os.environ.get("GHL_LIVE_WRITE") != "1":
        raise ValueError("live-write requires GHL_LIVE_WRITE=1 and only disposable test records are allowed")

    env = _base_env(mode)
    results: list[StressResult] = []
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    prefix = f"ghlcli-test-{timestamp}"

    with tempfile.TemporaryDirectory(prefix="ghlcli-stress-") as tmp:
        output_file = Path(tmp) / "workflow-steps.json"
        matrices: list[tuple[str, list[str]]] = []
        if mode == "mock":
            matrices.extend(_help_matrix())
            matrices.append(("generic request dry-run", ["--json", "request", "GET", "/contacts/", "--dry-run"]))
        else:
            matrices.extend(_help_matrix())
            matrices.extend(_dry_run_matrix(output_file))
        if mode in {"live-read", "live-write"}:
            matrices.extend(_live_read_matrix())
            if include_agency:
                agency_pit = env.get("GHL_TEST_AGENCY_PIT", "").strip()
                if agency_pit:
                    agency_env = dict(env)
                    agency_env["GHL_API_KEY"] = agency_pit
                    for name, args in _agency_matrix(agency_env):
                        results.append(_run_cli(args, mode, agency_env, name, timeout))
                else:
                    _append_skipped(results, mode, "agency preflight", "GHL_TEST_AGENCY_PIT not supplied")

        for name, args in matrices:
            results.append(_run_cli(args, mode, env, name, timeout))

        if mode == "live-write":
            _run_live_writes(results, env, timeout, prefix)

    summary_counts = {status: sum(1 for item in results if item.status == status) for status in ("passed", "failed", "skipped")}
    payload = {
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "prefix": prefix if mode == "live-write" else None,
        "ok": summary_counts["failed"] == 0,
        "summary": {
            "total": len(results),
            **summary_counts,
        },
        "results": [asdict(item) for item in results],
        "coverage": build_endpoint_coverage(cli) if cli is not None else None,
    }
    payload = redact(payload, env)
    path = _report_path(Path(report_dir), mode)
    _write_report(path, payload)
    payload["report_path"] = str(path)
    return payload
