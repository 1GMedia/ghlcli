"""OAuth helpers ported from the Go/PHP SDK patterns."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


OAUTH_TOKEN_URL = "https://services.leadconnectorhq.com/oauth/token"
LOCATION_TOKEN_URL = "https://services.leadconnectorhq.com/oauth/locationToken"
DEFAULT_VERSION = "2021-07-28"


def _form_headers() -> dict[str, str]:
    return {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}


class OAuthClient:
    """Small synchronous OAuth client for HighLevel."""

    def __init__(self, client_id: str, client_secret: str, timeout: int = 30):
        if not client_id:
            raise ValueError("GHL_CLIENT_ID is required")
        if not client_secret:
            raise ValueError("GHL_CLIENT_SECRET is required")
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OAuthClient":
        return cls(
            os.environ.get("GHL_CLIENT_ID", "").strip(),
            os.environ.get("GHL_CLIENT_SECRET", "").strip(),
        )

    def exchange_code(self, code: str, redirect_uri: str, user_type: str | None = None) -> dict:
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        }
        if user_type:
            data["user_type"] = user_type
        return self._post_token(data)

    def refresh(self, refresh_token: str) -> dict:
        return self._post_token(
            {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )

    def location_token(self, company_token: str, company_id: str, location_id: str) -> dict:
        response = requests.post(
            LOCATION_TOKEN_URL,
            headers={
                "Authorization": f"Bearer {company_token}",
                "Version": DEFAULT_VERSION,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={"companyId": company_id, "locationId": location_id},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _post_token(self, data: dict[str, str]) -> dict:
        response = requests.post(
            OAUTH_TOKEN_URL,
            headers=_form_headers(),
            data=data,
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()


def default_token_store_path() -> Path:
    return Path(os.environ.get("GHLCLI_TOKEN_STORE", "~/.config/ghlcli/tokens.json")).expanduser()


def save_profile(profile: str, token_data: dict[str, Any], path: Path | None = None) -> Path:
    """Save OAuth token data under a named local profile."""
    store_path = path or default_token_store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if store_path.exists():
        existing = json.loads(store_path.read_text())
    existing[profile] = token_data
    store_path.write_text(json.dumps(existing, indent=2, sort_keys=True))
    try:
        store_path.chmod(0o600)
    except OSError:
        pass
    return store_path


def load_profile(profile: str, path: Path | None = None) -> dict[str, Any] | None:
    store_path = path or default_token_store_path()
    if not store_path.exists():
        return None
    data = json.loads(store_path.read_text())
    value = data.get(profile)
    return value if isinstance(value, dict) else None


def redact_token_response(data: dict[str, Any]) -> dict[str, Any]:
    """Return token response metadata with secrets redacted."""
    redacted = dict(data)
    for key in ("access_token", "refresh_token"):
        if key in redacted and redacted[key]:
            value = str(redacted[key])
            redacted[key] = value[:8] + "..."
    return redacted
