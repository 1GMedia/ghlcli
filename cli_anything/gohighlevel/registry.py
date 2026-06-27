"""Capability registry loading for ghlcli."""
from __future__ import annotations

import json
from importlib import resources
from typing import Iterable


_STABILITY_RANK = {"stable": 0, "experimental": 1, "planned": 2}
_PROVIDER_RANK = {
    "official-public-api": 0,
    "official-oauth": 1,
    "internal-workflows": 2,
    "local-builder": 3,
    "mcp-wrapper": 4,
}


def load_capabilities() -> dict:
    with resources.files("cli_anything.gohighlevel").joinpath("capabilities.json").open() as f:
        return json.load(f)


def iter_commands(
    provider: str | None = None,
    stability: str | None = None,
    auth: str | None = None,
) -> Iterable[dict]:
    for command in load_capabilities().get("commands", []):
        if provider and command.get("provider") != provider:
            continue
        if stability and command.get("stability") != stability:
            continue
        if auth and command.get("auth") != auth:
            continue
        yield command


def canonical_key(command: dict) -> tuple[str, str]:
    """Return a stable merge key for endpoint-backed capabilities."""
    endpoint = str(command.get("endpoint") or "")
    if " " in endpoint and not endpoint.startswith("POST/PUT "):
        method, path = endpoint.split(" ", 1)
        return method.upper(), path
    return "COMMAND", str(command.get("name") or command.get("command") or "")


def merge_duplicate_capabilities(commands: Iterable[dict] | None = None) -> list[dict]:
    """Merge duplicate capabilities while preserving source variants."""
    merged: dict[tuple[str, str], dict] = {}
    for command in commands if commands is not None else load_capabilities().get("commands", []):
        key = canonical_key(command)
        existing = merged.get(key)
        variant = {
            "name": command.get("name"),
            "command": command.get("command"),
            "provider": command.get("provider"),
            "auth": command.get("auth"),
            "stability": command.get("stability"),
        }
        if existing is None:
            item = dict(command)
            item["sources"] = [variant]
            merged[key] = item
            continue
        existing["sources"].append(variant)
        current_rank = (
            _STABILITY_RANK.get(str(existing.get("stability")), 9),
            _PROVIDER_RANK.get(str(existing.get("provider")), 9),
        )
        candidate_rank = (
            _STABILITY_RANK.get(str(command.get("stability")), 9),
            _PROVIDER_RANK.get(str(command.get("provider")), 9),
        )
        if candidate_rank < current_rank:
            sources = existing["sources"]
            replacement = dict(command)
            replacement["sources"] = sources
            merged[key] = replacement
    return list(merged.values())
