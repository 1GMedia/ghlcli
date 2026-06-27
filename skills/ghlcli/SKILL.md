---
name: ghlcli
description: Use unofficial GoHighLevel CLI for public API commands, endpoint/spec discovery, QA stress testing, protected Firebase/internal workflow tooling. Use when user mentions ghlcli, GoHighLevel CLI, LeadConnector CLI, GHL workflows, GHL contacts, HighLevel MCP, packaging CLI agent skill.
---
# ghlcli
Use this skill when working in the `ghlcli` project or operating the unofficial GoHighLevel CLI.

## Core Rules
- Keep public API, MCP/spec catalog, and Firebase/internal lanes clearly separated.
- Use live credentials only through ephemeral environment variables.
- Do not store PITs, Firebase tokens, OAuth tokens, or live response dumps in repo files.
- Prefer dry-run and mock QA before live calls.
- Keep claims exact: this CLI does not have more official public endpoints than HighLevel, but it does combine public API coverage, MCP/spec discovery, and guarded internal workflow operations.

## Start
```bash
cd "/Users/gavinbasuel/Documents/GHL CLI"
./ghl doctor --json
./ghl endpoints coverage --json
./ghl qa stress --mode dry-run --json
```

## References
- Read `references/positioning.md` before making claims about Firebase/internal workflow access.
- Read `references/safety.md` before running live or mutating commands.
- Read `references/packaging.md` before changing npm/npx or skill packaging.

## Common Commands
```bash
./ghl --help
./ghl capabilities list --merged --json
./ghl request GET /contacts/ --dry-run --json
./ghl --experimental internal request GET '/workflow/{locationId}' --path-param locationId=<location_id> --dry-run --json
```

## Validation
Before saying packaging or CLI changes are done, run:

```bash
.venv/bin/python -m py_compile cli_anything/gohighlevel/*.py cli_anything/gohighlevel/auth/*.py cli_anything/gohighlevel/adapters/*.py cli_anything/gohighlevel/utils/*.py tests/*.py
.venv/bin/python -m unittest discover -s tests -v
./ghl qa stress --mode dry-run --json
npm pack --dry-run
npx --yes skills add ./ --list
```

## Done Means
- `AGENTS.md` carries passive repo context.
- This skill remains under `skills/ghlcli/SKILL.md`.
- `name: ghlcli` matches the parent folder.
- `ghlcli-skill install` copies the full skill folder, including references.
- npx wrappers still launch the Python CLI.
- Secret scans find no real PITs or Firebase/session tokens.
