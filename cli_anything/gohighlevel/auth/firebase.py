"""Firebase session-token diagnostics for internal workflow commands."""
from __future__ import annotations

import os


def status(env: dict[str, str] | None = None) -> dict:
    """Return redacted Firebase auth status for diagnostics."""
    values = env or os.environ
    refresh = values.get("GHL_FIREBASE_REFRESH_TOKEN", "").strip()
    direct = values.get("GHL_FIREBASE_TOKEN", "").strip()
    return {
        "refresh_token": bool(refresh),
        "refresh_token_prefix": refresh[:8] + "..." if refresh else None,
        "direct_token": bool(direct),
        "direct_token_prefix": direct[:8] + "..." if direct else None,
        "usable": bool(refresh or direct),
    }
