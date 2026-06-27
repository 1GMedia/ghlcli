from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import click
from click.testing import CliRunner

from cli_anything.gohighlevel import coverage, qa_stress
from cli_anything.gohighlevel.gohighlevel_cli import cli


class QaStressSafetyTests(unittest.TestCase):
    def test_redacts_pit_from_text_and_nested_data(self):
        token = "pit-00000000-0000-4000-8000-000000000000"
        env = {"GHL_TEST_SUBACCOUNT_PIT": token}

        text = qa_stress.redact(f"Authorization: Bearer {token}", env)
        nested = qa_stress.redact({"stdout": token, "items": [f"token={token}"]}, env)

        self.assertNotIn(token, text)
        self.assertNotIn(token, json.dumps(nested))
        self.assertIn("pit-[redacted]", text)

    def test_live_read_requires_test_env(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "GHL_TEST_SUBACCOUNT_PIT"):
                qa_stress.run_stress(mode="live-read")

    def test_live_write_requires_explicit_flag(self):
        env = {
            "GHL_TEST_SUBACCOUNT_PIT": "pit-test",
            "GHL_TEST_LOCATION_ID": "loc-test",
        }
        with patch.dict(os.environ, env, clear=True):
            with self.assertRaisesRegex(ValueError, "GHL_LIVE_WRITE=1"):
                qa_stress.run_stress(mode="live-write")


class EndpointCoverageTests(unittest.TestCase):
    def test_classifies_native_and_gateway_only_categories(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp)
            (spec_dir / "contacts.json").write_text(
                json.dumps({"paths": {"/contacts/": {"get": {"summary": "List", "operationId": "list"}}}})
            )
            (spec_dir / "blogs.json").write_text(
                json.dumps({"paths": {"/blogs/posts": {"get": {"summary": "Posts", "operationId": "posts"}}}})
            )

            cli = click.Group()
            cli.add_command(click.Group("contacts"))

            with patch.dict(os.environ, {"GHLCLI_SPEC_DIR": str(spec_dir)}):
                with patch("cli_anything.gohighlevel.coverage.mcp_inventory.list_tools", return_value=[]):
                    report = coverage.build_endpoint_coverage(cli)

        by_category = {row["category"]: row for row in report["categories"]}
        self.assertEqual(by_category["contacts"]["status"], "native")
        self.assertEqual(by_category["blogs"]["status"], "gateway-only")
        self.assertEqual(report["summary"]["endpoints"], 2)


class NativeCommandShapeTests(unittest.TestCase):
    def test_contacts_search_uses_page_limit(self):
        runner = CliRunner()
        with patch("cli_anything.gohighlevel.gohighlevel_cli.api.post", return_value={"ok": True}) as post:
            result = runner.invoke(cli, ["--location-id", "loc-1", "contacts", "search", "Bob", "--limit", "7"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(post.call_args.args[0], "/contacts/search")
        self.assertEqual(post.call_args.kwargs["data"]["pageLimit"], 7)
        self.assertNotIn("pageSize", post.call_args.kwargs["data"])

    def test_opportunities_list_uses_snake_case_location(self):
        runner = CliRunner()
        with patch("cli_anything.gohighlevel.gohighlevel_cli.api.get", return_value={"ok": True}) as get:
            result = runner.invoke(
                cli,
                ["--location-id", "loc-1", "opportunities", "list", "--pipeline-id", "pipe-1", "--limit", "3"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(get.call_args.args[0], "/opportunities/search")
        self.assertEqual(get.call_args.kwargs["params"]["location_id"], "loc-1")
        self.assertEqual(get.call_args.kwargs["params"]["pipeline_id"], "pipe-1")
        self.assertNotIn("locationId", get.call_args.kwargs["params"])

    def test_social_posts_uses_path_location_and_string_pagination(self):
        runner = CliRunner()
        with patch("cli_anything.gohighlevel.gohighlevel_cli.api.post", return_value={"ok": True}) as post:
            result = runner.invoke(
                cli,
                ["--location-id", "loc-1", "social", "posts", "--limit", "4", "--offset", "2"],
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(post.call_args.args[0], "/social-media-posting/loc-1/posts/list")
        self.assertEqual(post.call_args.kwargs["data"]["limit"], "4")
        self.assertEqual(post.call_args.kwargs["data"]["skip"], "2")
        self.assertNotIn("locationId", post.call_args.kwargs["data"])

    def test_forms_list_includes_location_id(self):
        runner = CliRunner()
        with patch("cli_anything.gohighlevel.gohighlevel_cli.api.get", return_value={"ok": True}) as get:
            result = runner.invoke(cli, ["--location-id", "loc-1", "forms", "list", "--limit", "4"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(get.call_args.args[0], "/forms/")
        self.assertEqual(get.call_args.kwargs["params"]["locationId"], "loc-1")
        self.assertEqual(get.call_args.kwargs["params"]["limit"], 4)

    def test_contacts_remove_tag_sends_delete_body(self):
        runner = CliRunner()
        with patch("cli_anything.gohighlevel.gohighlevel_cli.api.delete", return_value={"ok": True}) as delete:
            result = runner.invoke(cli, ["contacts", "remove-tag", "contact-1", "qa-tag"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(delete.call_args.args[0], "/contacts/contact-1/tags")
        self.assertEqual(delete.call_args.kwargs["data"], {"tags": ["qa-tag"]})


class InternalRequestCommandTests(unittest.TestCase):
    def test_internal_request_dry_run_resolves_location_without_token(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--experimental",
                "--location-id",
                "loc-1",
                "internal",
                "request",
                "GET",
                "/workflow/{locationId}",
                "--dry-run",
                "--json",
            ],
        )

        self.assertEqual(result.exit_code, 0, result.output)
        data = json.loads(result.output)
        self.assertEqual(data["base_url"], "https://backend.leadconnectorhq.com")
        self.assertEqual(data["path"], "/workflow/loc-1")
        self.assertEqual(data["auth"], "firebase-session")
        self.assertFalse(data["mutates"])

    def test_internal_request_requires_experimental_flag(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["internal", "request", "GET", "/workflow/test", "--dry-run"])

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--experimental", result.output)

    def test_internal_mutating_request_requires_confirm(self):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--experimental", "--location-id", "loc-1", "internal", "request", "POST", "/workflow/loc-1"],
        )

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("--confirm", result.output)


if __name__ == "__main__":
    unittest.main()
