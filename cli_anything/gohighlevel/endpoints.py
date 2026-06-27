"""Endpoint catalog backed by open-ghl-mcp specs."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Endpoint:
    category: str
    method: str
    path: str
    summary: str
    operation_id: str


def _candidate_spec_dirs() -> list[Path]:
    candidates: list[Path] = []
    env_dir = os.environ.get("GHLCLI_SPEC_DIR")
    if env_dir:
        candidates.append(Path(env_dir).expanduser())

    here = Path(__file__).resolve()
    for parent in here.parents:
        candidates.append(parent / "upstreams" / "open-ghl-mcp" / "specs" / "ghl")
    candidates.append(Path.cwd() / "upstreams" / "open-ghl-mcp" / "specs" / "ghl")
    return candidates


def find_spec_dir() -> Path | None:
    for candidate in _candidate_spec_dirs():
        if candidate.exists() and any(candidate.glob("*.json")):
            return candidate
    return None


def require_spec_dir() -> Path:
    spec_dir = find_spec_dir()
    if not spec_dir:
        raise FileNotFoundError(
            "Could not find open-ghl-mcp specs. Set GHLCLI_SPEC_DIR or clone upstreams/open-ghl-mcp."
        )
    return spec_dir


def list_categories() -> list[str]:
    spec_dir = require_spec_dir()
    return sorted(path.stem for path in spec_dir.glob("*.json"))


def load_spec(category: str) -> dict:
    spec_path = require_spec_dir() / f"{category}.json"
    if not spec_path.exists():
        raise FileNotFoundError(f"Unknown endpoint category: {category}")
    return json.loads(spec_path.read_text())


def iter_endpoints(category: str | None = None) -> Iterable[Endpoint]:
    categories = [category] if category else list_categories()
    for cat in categories:
        data = load_spec(cat)
        for path, methods in data.get("paths", {}).items():
            for method, meta in methods.items():
                yield Endpoint(
                    category=cat,
                    method=method.upper(),
                    path=path,
                    summary=meta.get("summary", ""),
                    operation_id=meta.get("operationId", ""),
                )


def search_endpoints(query: str, category: str | None = None) -> list[Endpoint]:
    """Search endpoint category, method, path, summary, and operation ID."""
    needle = query.lower().strip()
    if not needle:
        return list(iter_endpoints(category))

    results: list[Endpoint] = []
    for endpoint in iter_endpoints(category):
        haystack = " ".join(
            [
                endpoint.category,
                endpoint.method,
                endpoint.path,
                endpoint.summary,
                endpoint.operation_id,
            ]
        ).lower()
        if needle in haystack:
            results.append(endpoint)
    return results


def catalog_status() -> dict:
    spec_dir = find_spec_dir()
    if not spec_dir:
        return {"available": False, "path": None, "categories": 0, "endpoints": 0}

    categories = sorted(spec_dir.glob("*.json"))
    endpoint_count = 0
    for path in categories:
        try:
            data = json.loads(path.read_text())
            endpoint_count += sum(len(methods) for methods in data.get("paths", {}).values())
        except Exception:
            pass
    return {
        "available": True,
        "path": str(spec_dir),
        "categories": len(categories),
        "endpoints": endpoint_count,
    }
