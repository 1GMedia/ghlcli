"""Coverage reporting for the unofficial HighLevel CLI."""

from __future__ import annotations

from collections import Counter
from typing import Any

import click

from cli_anything.gohighlevel import endpoints, mcp_inventory


CATEGORY_COMMAND_ALIASES = {
    "calendars": "calendars",
    "contacts": "contacts",
    "conversations": "conversations",
    "documents": "documents",
    "emails": "emails",
    "forms": "forms",
    "invoices": "payments",
    "locations": "locations",
    "opportunities": "opportunities",
    "payments": "payments",
    "social-media-posting": "social",
    "social-planner": "social",
    "workflows": "workflows",
}


def _tool_categories() -> set[str]:
    categories: set[str] = set()
    for tool in mcp_inventory.list_tools("open-ghl-mcp"):
        file_stem = tool.file.rsplit("/", 1)[-1].removesuffix(".py")
        if file_stem:
            categories.add(file_stem.replace("_", "-"))
    return categories


def _native_groups(cli: click.Group) -> set[str]:
    return {
        name
        for name, command in cli.commands.items()
        if isinstance(command, click.Group)
    }


def build_endpoint_coverage(cli: click.Group) -> dict[str, Any]:
    """Compare native command groups with the open-ghl-mcp endpoint catalog."""
    native_groups = _native_groups(cli)
    catalog_categories = set(endpoints.list_categories())
    mcp_categories = _tool_categories()
    rows = []

    for category in sorted(catalog_categories | mcp_categories):
        mapped_group = CATEGORY_COMMAND_ALIASES.get(category, category)
        endpoint_count = sum(1 for _ in endpoints.iter_endpoints(category)) if category in catalog_categories else 0
        has_native = mapped_group in native_groups
        has_mcp = category in mcp_categories

        if has_native and endpoint_count:
            status = "native"
        elif endpoint_count:
            status = "gateway-only"
        elif has_mcp:
            status = "mcp-only"
        else:
            status = "missing"

        rows.append(
            {
                "category": category,
                "status": status,
                "native_group": mapped_group if has_native else None,
                "endpoint_count": endpoint_count,
                "mcp_tools": has_mcp,
            }
        )

    counts = Counter(row["status"] for row in rows)
    return {
        "summary": {
            "categories": len(rows),
            "endpoints": sum(row["endpoint_count"] for row in rows),
            "native": counts["native"],
            "gateway_only": counts["gateway-only"],
            "mcp_only": counts["mcp-only"],
            "missing": counts["missing"],
        },
        "categories": rows,
    }
