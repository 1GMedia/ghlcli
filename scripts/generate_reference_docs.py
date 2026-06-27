#!/usr/bin/env python3
"""Generate GitHub-facing CLI SDK reference docs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import click

from cli_anything.gohighlevel import coverage, registry
from cli_anything.gohighlevel.gohighlevel_cli import cli

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOCS = ROOT / "docs"
SKILLS_DIR = ROOT / "skills"


def _command_rows(group: click.Group, prefix: tuple[str, ...] = ()) -> list[dict]:
    rows: list[dict] = []
    for name, command in sorted(group.commands.items()):
        parts = (*prefix, name)
        rows.append(
            {
                "command": " ".join(("ghl", *parts)),
                "help": command.short_help or command.help or "",
                "children": sorted(command.commands) if isinstance(command, click.Group) else [],
            }
        )
        if isinstance(command, click.Group):
            rows.extend(_command_rows(command, parts))
    return rows


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n")
    return path


def _commands_doc() -> str:
    rows = _command_rows(cli)
    lines = [
        "# ghlcli Command Reference",
        "",
        "Generated from the Click command tree. Rebuild with `python scripts/generate_reference_docs.py`.",
        "",
        "| Command | Description | Subcommands |",
        "|---|---|---|",
    ]
    for row in rows:
        children = ", ".join(f"`{child}`" for child in row["children"]) if row["children"] else ""
        lines.append(f"| `{row['command']}` | {row['help']} | {children} |")
    return "\n".join(lines)


def _endpoint_doc() -> str:
    try:
        report = coverage.build_endpoint_coverage(cli)
    except Exception as exc:
        report = {"summary": {"error": str(exc)}, "categories": []}
    summary = report.get("summary", {})
    lines = [
        "# Endpoint Coverage Map",
        "",
        "Generated from `capabilities.json`, native Click groups, and the open-ghl-mcp endpoint catalog.",
        "",
        "## Summary",
        "",
        "```json",
        json.dumps(summary, indent=2, sort_keys=True),
        "```",
        "",
        "| Category | Status | Native Group | Endpoints | MCP Tools |",
        "|---|---|---|---:|---|",
    ]
    for row in report.get("categories", []):
        lines.append(
            "| `{category}` | `{status}` | {native} | {count} | {mcp} |".format(
                category=row["category"],
                status=row["status"],
                native=f"`{row['native_group']}`" if row.get("native_group") else "",
                count=row.get("endpoint_count", 0),
                mcp="yes" if row.get("mcp_tools") else "no",
            )
        )
    lines.extend(
        [
            "",
            "## Capability Registry",
            "",
            "| Capability | CLI | SDK Helper | Provider | Auth | Mutates | Endpoint |",
            "|---|---|---|---|---|---|---|",
        ]
    )
    for item in registry.merge_duplicate_capabilities():
        lines.append(
            "| `{name}` | `{command}` | `{sdk}` | `{provider}` | `{auth}` | `{mutates}` | `{endpoint}` |".format(
                name=item.get("name", ""),
                command=item.get("command", ""),
                sdk=item.get("sdk", ""),
                provider=item.get("provider", ""),
                auth=item.get("auth", ""),
                mutates=item.get("mutates", ""),
                endpoint=item.get("endpoint", ""),
            )
        )
    return "\n".join(lines)


def _sdk_doc() -> str:
    return """# Python SDK

`ghlcli` exposes an importable Python SDK for the public HighLevel API lane.
The SDK does not use Firebase/internal workflow access by default.

```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
contacts = client.contacts.list(limit=10)
result = client.request("GET", "/contacts/", params={"locationId": client.location_id})
```

## Auth

`GHLClient(api_key=None, location_id=None, version=None)` resolves credentials in this order:

1. explicit constructor arguments
2. environment variables `GHL_API_KEY` and `GHL_LOCATION_ID`

## Resource Helpers

The SDK includes helpers for native CLI groups:

- `client.contacts`
- `client.conversations`
- `client.workflows`
- `client.opportunities`
- `client.calendars`
- `client.locations`
- `client.payments`
- `client.forms`
- `client.social`
- `client.documents`
- `client.emails`

Use `client.request(method, path, body=None, params=None, path_params=None)` for long-tail endpoints.
"""


def _skill_rows() -> Iterable[tuple[str, str]]:
    for skill in sorted(SKILLS_DIR.glob("ghlcli*/SKILL.md")):
        name = skill.parent.name
        description = ""
        for line in skill.read_text().splitlines():
            if line.startswith("description:"):
                description = line.split(":", 1)[1].strip()
                break
        yield name, description


def _skills_doc() -> str:
    lines = [
        "# Agent Skills",
        "",
        "Generated from `skills/ghlcli*` skill folders.",
        "",
        "| Skill | Purpose |",
        "|---|---|",
    ]
    for name, description in _skill_rows():
        lines.append(f"| `{name}` | {description} |")
    lines.extend(
        [
            "",
            "Install/discover locally:",
            "",
            "```bash",
            "npx --yes skills add ./ --list",
            "npx --yes skills add ./ --skill ghlcli -y",
            "```",
        ]
    )
    return "\n".join(lines)


def generate_docs(output_dir: Path = DEFAULT_DOCS) -> list[Path]:
    return [
        _write(output_dir / "commands.md", _commands_doc()),
        _write(output_dir / "endpoint-map.md", _endpoint_doc()),
        _write(output_dir / "python-sdk.md", _sdk_doc()),
        _write(output_dir / "agent-skills.md", _skills_doc()),
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DOCS)
    args = parser.parse_args()
    for path in generate_docs(args.output_dir):
        print(path)


if __name__ == "__main__":
    main()
