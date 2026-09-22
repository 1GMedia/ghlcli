"""Crash, concurrency and identity regressions with an in-memory fake provider."""
import copy
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from cli_anything.gohighlevel.gohighlevel_cli import cli
from cli_anything.gohighlevel.artist_provisioning import (
    MASTER_LOCATION, ReceiptStore, SetupError, plan_artist, run_setup,
)


class Provider:
    def __init__(self, plan):
        self.plan = plan
        self.pipelines = self
        self.rows = {"pipelines": [], "tags": []}
        self.calls = []
        self.timeout_kind = None
        self.hide = False
        self.create_hook = None

    def require_location_id(self):
        return MASTER_LOCATION

    def list(self):
        self.calls.append("GET pipelines")
        return {"pipelines": [] if self.hide else copy.deepcopy(self.rows["pipelines"])}

    def create(self, *, name, stages):
        self.calls.append("POST pipeline")
        row = {"id": "pipeline-1", "name": name, "locationId": MASTER_LOCATION,
               "stages": [{"id": f"stage-{i}", "name": name} for i, name in enumerate(stages)]}
        self.rows["pipelines"].append(row)
        if self.create_hook:
            self.create_hook()
        if self.timeout_kind == "pipeline":
            raise TimeoutError("secret response that must not leak")
        return copy.deepcopy(row)

    def request(self, method, path, **kwargs):
        assert path == "/locations/{locationId}/tags"
        assert kwargs["version"] == "v3"
        self.calls.append(method + " tags")
        if method == "GET":
            return {"tags": copy.deepcopy(self.rows["tags"])}
        row = {"id": "tag-1", "name": kwargs["body"]["name"], "locationId": MASTER_LOCATION}
        self.rows["tags"].append(row)
        if self.timeout_kind == "tag":
            raise TimeoutError("secret response that must not leak")
        return {"tag": row}


class SetupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "receipts.sqlite"
        self.store = ReceiptStore(self.path)
        self.addCleanup(self.store.close)
        self.plan = plan_artist(94, "Example Artist")
        self.provider = Provider(self.plan)
        self.env = patch.dict(os.environ, {"TAT100_GHL_ROLLOUT_ENABLED": "true"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def run_setup(self, apply=True, **kwargs):
        return run_setup(self.provider, self.store, self.plan, apply=apply,
                         confirm_location=MASTER_LOCATION, proof="TAT-99 reviewed", **kwargs)

    def test_default_read_only_never_creates(self):
        result = self.run_setup(apply=False)
        self.assertEqual(result["status"], "ready_for_apply")
        self.assertFalse(any(c.startswith("POST") for c in self.provider.calls))

    def test_one_create_per_run_then_readback_with_stable_ids(self):
        first = self.run_setup()
        self.assertEqual(first["status"], "resume_required")
        self.assertEqual(first["operations"]["pipeline"]["remote_id"], "pipeline-1")
        second = self.run_setup()
        self.assertEqual(second["status"], "verified_for_admin_binding")
        self.assertEqual(second["operations"]["tag"]["remote_id"], "tag-1")
        self.run_setup()
        self.assertEqual(self.provider.calls.count("POST pipeline"), 1)
        self.assertEqual(self.provider.calls.count("POST tags"), 1)

    def test_pipeline_timeout_restart_reconciles_without_duplicate(self):
        self.provider.timeout_kind = "pipeline"
        result = self.run_setup()
        self.assertEqual(result["status"], "needs_reconciliation")
        self.assertNotIn("secret response", str(result))
        with ReceiptStoreContext(self.path) as other:
            result = run_setup(self.provider, other, self.plan)
        self.assertEqual(result["operations"]["pipeline"]["remote_id"], "pipeline-1")
        self.assertEqual(self.provider.calls.count("POST pipeline"), 1)

    def test_timeout_not_found_never_recreates(self):
        self.provider.timeout_kind = "pipeline"
        self.run_setup()
        self.provider.rows["pipelines"] = []
        for _ in range(3):
            self.assertEqual(self.run_setup()["status"], "needs_reconciliation")
        self.assertEqual(self.provider.calls.count("POST pipeline"), 1)

    def test_tag_timeout_preserves_pipeline_and_reconciles(self):
        self.run_setup()
        self.provider.timeout_kind = "tag"
        self.assertEqual(self.run_setup()["status"], "needs_reconciliation")
        result = self.run_setup(apply=False)
        self.assertEqual(result["status"], "verified_for_admin_binding")
        self.assertEqual(self.provider.calls.count("POST tags"), 1)

    def test_marker_committed_before_remote_call_and_concurrent_process_cannot_claim(self):
        def hook():
            with ReceiptStoreContext(self.path) as other:
                self.assertEqual(other.get(self.plan, "pipeline")["state"], "creating")
                self.assertFalse(other.claim(self.plan, "pipeline"))
        self.provider.create_hook = hook
        self.run_setup()

    def test_crash_before_network_keeps_marker_even_with_no_remote_object(self):
        self.store.prepare(self.plan, "proof")
        self.assertTrue(self.store.claim(self.plan, "pipeline"))
        self.assertEqual(self.run_setup()["status"], "needs_reconciliation")
        self.assertNotIn("POST pipeline", self.provider.calls)

    def test_persisted_id_not_swapped_after_remote_deletion(self):
        self.run_setup()
        self.provider.rows["pipelines"][0]["id"] = "different-pipeline"
        result = self.run_setup()
        self.assertEqual(result["status"], "needs_review")
        self.assertEqual(result["operations"]["pipeline"]["remote_id"], "pipeline-1")
        self.assertNotIn("POST tags", self.provider.calls)

    def test_exact_existing_objects_reused_without_updates(self):
        self.provider.create(name=self.plan["pipelineName"], stages=self.plan["stages"])
        self.provider.request("POST", "/locations/{locationId}/tags", body={"name": self.plan["tagName"]}, version="v3")
        self.provider.calls.clear()
        self.assertEqual(self.run_setup(apply=False)["status"], "verified_for_admin_binding")
        self.assertTrue(all(c.startswith("GET") for c in self.provider.calls))

    def test_wrong_location_case_collision_stages_or_duplicate_match_blocks(self):
        for change in ("location", "case", "stage", "duplicate"):
            with self.subTest(change=change):
                self.provider.rows["pipelines"] = []
                self.provider.create(name=self.plan["pipelineName"], stages=self.plan["stages"])
                row = self.provider.rows["pipelines"][0]
                if change == "location": row["locationId"] = "another-location"
                if change == "case": row["name"] = row["name"].upper()
                if change == "stage": row["stages"][0]["name"] = "Edited by sales"
                if change == "duplicate": self.provider.rows["pipelines"].append(copy.deepcopy(row))
                self.provider.calls.clear()
                self.assertEqual(self.run_setup()["status"], "needs_review")
                self.assertTrue(all(c.startswith("GET") for c in self.provider.calls))

    def test_read_failure_never_proves_absence(self):
        with patch.object(self.provider, "list", return_value={"unexpected": []}):
            self.assertEqual(self.run_setup()["status"], "needs_review")
        with patch.object(self.provider, "list", return_value={"pipelines": [], "hasMore": True}):
            self.assertEqual(self.run_setup()["status"], "needs_review")
        self.assertNotIn("POST pipeline", self.provider.calls)

    def test_plan_change_cannot_discard_attempt(self):
        self.run_setup()
        with self.assertRaises(SetupError):
            run_setup(self.provider, self.store, plan_artist(94, "Renamed Artist"))

    def test_no_apply_without_gate_proof_and_location(self):
        for args in ({}, {"proof": "proof"}, {"confirm_location": MASTER_LOCATION}):
            with self.assertRaises(SetupError):
                run_setup(self.provider, self.store, self.plan, apply=True, **args)
        with patch.dict(os.environ, {"TAT100_GHL_ROLLOUT_ENABLED": "false"}), self.assertRaises(SetupError):
            self.run_setup()
        self.assertEqual(self.provider.calls, [])

    def test_create_response_id_retained_when_readback_unavailable(self):
        self.provider.create_hook = lambda: setattr(self.provider, "hide", True)
        result = self.run_setup()
        self.assertEqual(result["operations"]["pipeline"]["remote_id"], "pipeline-1")
        self.assertEqual(result["status"], "needs_reconciliation")
        self.assertEqual(self.run_setup()["status"], "needs_review")
        self.assertEqual(self.provider.calls.count("POST pipeline"), 1)

    def test_tampered_plan_rejected_before_network_or_receipt(self):
        for key, value in (("tagName", "another_artist"), ("stages", ["Arbitrary"]), ("version", 2)):
            with self.subTest(key=key), self.assertRaises(SetupError):
                run_setup(self.provider, self.store, dict(self.plan, **{key: value}))
        self.assertEqual(self.provider.calls, [])

    def test_permission_error_stays_uncertain_without_exposing_response(self):
        with patch.object(self.provider, "create", side_effect=RuntimeError("secret-token and provider body")):
            result = self.run_setup()
        self.assertEqual(result["operations"]["pipeline"]["state"], "creating")
        self.assertNotIn("secret-token", str(result))
        self.assertEqual(self.run_setup()["status"], "needs_reconciliation")
        self.assertNotIn("POST pipeline", self.provider.calls)

    def test_cli_plan_is_offline_and_rejects_ambiguous_artist_names(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["--json", "artist-setup", "plan", "--artist-id", "94", "--artist-name", "Example"])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertIn("tattoo_artist_94", result.output)
        with self.assertRaises(SetupError): plan_artist(94, "Imposter [93]")
        with self.assertRaises(SetupError): plan_artist(True, "Example")


class ReceiptStoreContext:
    def __init__(self, path): self.store = ReceiptStore(path)
    def __enter__(self): return self.store
    def __exit__(self, *args): self.store.close()
