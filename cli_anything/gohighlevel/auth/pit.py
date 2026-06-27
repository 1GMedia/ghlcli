"""Private Integration Token helpers."""
from __future__ import annotations

import os


DEFAULT_VERSION = "2021-07-28"


def get_token(env: dict[str, str] | None = None) -> str:
    """Return the configured public API bearer token, if any."""
    values = env or os.environ
    return values.get("GHL_API_KEY", "").strip()


def get_location_id(env: dict[str, str] | None = None) -> str:
    """Return the configured default location ID, if any."""
    values = env or os.environ
    return values.get("GHL_LOCATION_ID", "").strip()


def build_headers(
    token: str | None = None,
    version: str = DEFAULT_VERSION,
    env: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build public HighLevel API headers."""
    bearer = token or get_token(env)
    if not bearer:
        raise ValueError("GHL_API_KEY is not set")
    return {
        "Authorization": f"Bearer {bearer}",
        "Version": version,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def status(env: dict[str, str] | None = None) -> dict:
    """Return redacted PIT/location status for diagnostics."""
    token = get_token(env)
    location_id = get_location_id(env)
    return {
        "api_key": bool(token),
        "api_key_prefix": token[:8] + "..." if token else None,
        "location_id": bool(location_id),
        "location_id_value": location_id if location_id and location_id != "YOUR_LOCATION_ID" else None,
        "location_id_placeholder": location_id == "YOUR_LOCATION_ID",
    }
