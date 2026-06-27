"""Generic public HighLevel API adapter."""
from __future__ import annotations

from typing import Any

import requests

from cli_anything.gohighlevel.auth.pit import build_headers


BASE_URL = "https://services.leadconnectorhq.com"


def request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | list[Any] | None = None,
    params: dict[str, Any] | None = None,
    version: str = "2021-07-28",
    token: str | None = None,
) -> dict[str, Any] | list[Any] | str:
    normalized_path = path if path.startswith("/") else "/" + path
    response = requests.request(
        method.upper(),
        f"{BASE_URL}{normalized_path}",
        headers=build_headers(token=token, version=version),
        params=params or None,
        json=body,
        timeout=30,
    )
    response.raise_for_status()
    if not response.content:
        return {"statusCode": response.status_code}
    try:
        return response.json()
    except ValueError:
        return response.text
