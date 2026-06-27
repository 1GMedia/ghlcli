from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from cli_anything.gohighlevel.sdk import GHLClient


class SDKClientTests(unittest.TestCase):
    def test_explicit_values_win_over_env(self):
        env = {"GHL_API_KEY": "env-token", "GHL_LOCATION_ID": "env-location"}
        with patch.dict("os.environ", env, clear=True):
            client = GHLClient(api_key="explicit-token", location_id="explicit-location", version="v3")

        self.assertEqual(client.api_key, "explicit-token")
        self.assertEqual(client.location_id, "explicit-location")
        self.assertEqual(client.headers()["Authorization"], "Bearer explicit-token")
        self.assertEqual(client.headers()["Version"], "v3")

    @patch("cli_anything.gohighlevel.sdk.client.requests.request")
    def test_request_resolves_path_params(self, request):
        response = Mock()
        response.content = b'{"ok": true}'
        response.json.return_value = {"ok": True}
        response.raise_for_status.return_value = None
        request.return_value = response

        client = GHLClient(api_key="token", location_id="loc-1")
        result = client.request("GET", "/locations/{locationId}/tags")

        self.assertEqual(result, {"ok": True})
        self.assertEqual(request.call_args.args[1], "https://services.leadconnectorhq.com/locations/loc-1/tags")
        self.assertEqual(request.call_args.kwargs["headers"]["Authorization"], "Bearer token")

    @patch("cli_anything.gohighlevel.sdk.client.requests.request")
    def test_contacts_list_shape(self, request):
        response = Mock()
        response.content = b'{"contacts": []}'
        response.json.return_value = {"contacts": []}
        response.raise_for_status.return_value = None
        request.return_value = response

        client = GHLClient(api_key="token", location_id="loc-1")
        client.contacts.list(limit=3)

        self.assertEqual(request.call_args.args[0], "GET")
        self.assertEqual(request.call_args.args[1], "https://services.leadconnectorhq.com/contacts/")
        self.assertEqual(request.call_args.kwargs["params"]["locationId"], "loc-1")
        self.assertEqual(request.call_args.kwargs["params"]["limit"], 3)

    @patch("cli_anything.gohighlevel.sdk.client.requests.request")
    def test_sdk_does_not_import_internal_client_for_default_usage(self, request):
        response = Mock()
        response.content = b'{}'
        response.json.return_value = {}
        response.raise_for_status.return_value = None
        request.return_value = response

        client = GHLClient(api_key="token", location_id="loc-1")
        self.assertFalse(hasattr(client, "internal"))
        client.conversations.send("conv-1", "hello")
        self.assertEqual(request.call_args.args[1], "https://services.leadconnectorhq.com/conversations/messages")


class DocsGeneratorTests(unittest.TestCase):
    def test_docs_generator_writes_reference_files(self):
        from scripts.generate_reference_docs import generate_docs

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            generated = generate_docs(out)

            names = {path.name for path in generated}
            self.assertIn("commands.md", names)
            self.assertIn("endpoint-map.md", names)
            self.assertIn("python-sdk.md", names)
            self.assertIn("agent-skills.md", names)
            self.assertIn("contacts", (out / "commands.md").read_text())
            self.assertIn("Coverage", (out / "endpoint-map.md").read_text())
            self.assertIn("ghlcli-contacts", (out / "agent-skills.md").read_text())


if __name__ == "__main__":
    unittest.main()
