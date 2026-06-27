from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from cli_anything.gohighlevel import endpoints, registry
from cli_anything.gohighlevel.auth.oauth import OAuthClient
from cli_anything.gohighlevel.auth.pit import build_headers
from cli_anything.gohighlevel.cli_extensions import _resolve_path
from cli_anything.gohighlevel.utils.ghl_internal_client import InternalGHLClient


class AuthTests(unittest.TestCase):
    def test_pit_headers(self):
        headers = build_headers(token="pit-test", version="v3")
        self.assertEqual(headers["Authorization"], "Bearer pit-test")
        self.assertEqual(headers["Version"], "v3")

    @patch("cli_anything.gohighlevel.auth.oauth.requests.post")
    def test_oauth_refresh(self, post):
        response = Mock()
        response.json.return_value = {"access_token": "new", "refresh_token": "next"}
        response.raise_for_status.return_value = None
        post.return_value = response

        result = OAuthClient("client", "secret").refresh("old-refresh")

        self.assertEqual(result["access_token"], "new")
        data = post.call_args.kwargs["data"]
        self.assertEqual(data["grant_type"], "refresh_token")
        self.assertEqual(data["refresh_token"], "old-refresh")

    @patch("cli_anything.gohighlevel.auth.oauth.requests.post")
    def test_location_token(self, post):
        response = Mock()
        response.json.return_value = {"access_token": "location-token"}
        response.raise_for_status.return_value = None
        post.return_value = response

        result = OAuthClient("client", "secret").location_token("company-token", "company", "location")

        self.assertEqual(result["access_token"], "location-token")
        self.assertEqual(post.call_args.kwargs["json"], {"companyId": "company", "locationId": "location"})


class InternalAuthTests(unittest.TestCase):
    def test_internal_client_rejects_placeholder_location(self):
        with self.assertRaises(SystemExit):
            InternalGHLClient(Mock(), "YB8rMdFShcHGcZGW87mA")

    def test_internal_client_trims_valid_location(self):
        client = InternalGHLClient(Mock(), " location-123 ")
        self.assertEqual(client.location_id, "location-123")


class RequestGatewayTests(unittest.TestCase):
    def test_resolve_path_uses_explicit_and_location_params(self):
        path = _resolve_path(
            "/locations/{locationId}/contacts/{contactId}",
            ("contactId=contact-123",),
            location_id="location-123",
        )
        self.assertEqual(path, "/locations/location-123/contacts/contact-123")

    def test_resolve_path_rejects_missing_params(self):
        with self.assertRaises(Exception):
            _resolve_path("/contacts/{contactId}", ())


class EndpointCatalogTests(unittest.TestCase):
    def test_endpoint_catalog_parses_specs(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec_dir = Path(tmp)
            (spec_dir / "contacts.json").write_text(
                json.dumps(
                    {
                        "paths": {
                            "/contacts/": {
                                "get": {"summary": "List Contacts", "operationId": "listContacts"}
                            }
                        }
                    }
                )
            )
            with patch("cli_anything.gohighlevel.endpoints.find_spec_dir", return_value=spec_dir):
                items = list(endpoints.iter_endpoints("contacts"))

                self.assertEqual(len(items), 1)
                self.assertEqual(items[0].method, "GET")
                self.assertEqual(items[0].path, "/contacts/")

                results = endpoints.search_endpoints("listcontacts", "contacts")
                self.assertEqual(len(results), 1)
                self.assertEqual(results[0].operation_id, "listContacts")


class RegistryTests(unittest.TestCase):
    def test_duplicate_merge_prefers_stable_official(self):
        items = registry.merge_duplicate_capabilities(
            [
                {
                    "name": "mcp.contacts.list",
                    "command": "ghl mcp call contacts.list",
                    "provider": "mcp-wrapper",
                    "auth": "provider-specific",
                    "stability": "planned",
                    "endpoint": "GET /contacts/",
                },
                {
                    "name": "contacts.list",
                    "command": "ghl contacts list",
                    "provider": "official-public-api",
                    "auth": "pit-or-oauth-location",
                    "stability": "stable",
                    "endpoint": "GET /contacts/",
                },
            ]
        )

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["name"], "contacts.list")
        self.assertEqual(len(items[0]["sources"]), 2)


if __name__ == "__main__":
    unittest.main()
