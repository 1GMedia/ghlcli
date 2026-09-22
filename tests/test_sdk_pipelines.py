"""Public pipeline contract tests; no live credentials or provider writes."""
from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from cli_anything.gohighlevel.sdk import GHLClient


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.client = GHLClient(api_key="test-token", location_id="test-location")
        self.transport = patch("cli_anything.gohighlevel.sdk.client.requests.request").start()
        self.addCleanup(patch.stopall)
        response = Mock(content=b'{"id":"pipeline-1"}')
        response.json.return_value = {"id": "pipeline-1"}
        response.raise_for_status.return_value = None
        self.transport.return_value = response

    def test_create_uses_configured_location_and_v3_without_changing_other_resources(self):
        result = self.client.pipelines.create(name=" Artist [93] ", stages=["New inquiry", "Contacted"])
        self.assertEqual(result, {"id": "pipeline-1"})
        args, kwargs = self.transport.call_args
        self.assertEqual(args, ("POST", "https://services.leadconnectorhq.com/opportunities/pipelines"))
        self.assertEqual(kwargs["headers"]["Version"], "v3")
        self.assertEqual(kwargs["json"], {
            "name": "Artist [93]", "locationId": "test-location",
            "stages": [{"name": "New inquiry", "position": 1}, {"name": "Contacted", "position": 2}],
        })
        self.assertEqual(self.client.headers()["Version"], "2021-07-28")

    def test_list_scopes_reconciliation_to_configured_location(self):
        self.client.pipelines.list()
        self.assertEqual(self.transport.call_args.args[0], "GET")
        self.assertEqual(self.transport.call_args.kwargs["params"], {"locationId": "test-location"})
        self.assertEqual(self.transport.call_args.kwargs["headers"]["Version"], "v3")

    def test_invalid_stages_never_reach_provider(self):
        for stages in ([], [""], ["New", " new "], [None], "New"):
            with self.subTest(stages=stages), self.assertRaises(ValueError):
                self.client.pipelines.create(name="Artist", stages=stages)
        self.transport.assert_not_called()

    def test_invalid_name_never_reaches_provider(self):
        for name in ("", "  ", None):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.client.pipelines.create(name=name, stages=["New"])
        self.transport.assert_not_called()

    def test_missing_location_never_reaches_provider(self):
        self.client.location_id = ""
        for action in (self.client.pipelines.list, lambda: self.client.pipelines.create(name="Artist", stages=["New"])):
            with self.assertRaises(ValueError):
                action()
        self.transport.assert_not_called()

    def test_call_cannot_override_location(self):
        with self.assertRaises(TypeError):
            self.client.pipelines.create(name="Artist", stages=["New"], locationId="other")
        self.transport.assert_not_called()

    def test_timeout_is_not_blindly_retried(self):
        self.transport.side_effect = requests.Timeout("unknown create outcome")
        with self.assertRaises(requests.Timeout):
            self.client.pipelines.create(name="Artist", stages=["New"])
        self.transport.assert_called_once()

    def test_permission_failure_is_not_treated_as_success(self):
        self.transport.return_value.raise_for_status.side_effect = requests.HTTPError("403")
        with self.assertRaises(requests.HTTPError):
            self.client.pipelines.create(name="Artist", stages=["New"])
        self.transport.assert_called_once()


if __name__ == "__main__":
    unittest.main()
