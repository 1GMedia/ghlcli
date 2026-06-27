# AGENTS.md

## Project

`ghlcli` is an unofficial Python-first GoHighLevel/LeadConnector CLI. It combines:

- Public/PIT API commands against `services.leadconnectorhq.com`.
- Endpoint/spec discovery from the cloned `open-ghl-mcp` catalog.
- A protected Firebase/internal workflow lane against `backend.leadconnectorhq.com`.
- A repeatable QA stress harness.

## Positioning Truth

Do say:

> `ghlcli` combines the official public API, MCP/spec endpoint catalog, and an experimental Firebase/internal workflow lane. It does not have more official public endpoints than HighLevel, but it can perform some UI/internal workflow operations that normal public API clients cannot.

Do not say:

> We can access everything in HighLevel.

The internal client is workflow-focused plus a guarded backend gateway.

## Safety

- Never commit `.env`, PITs, Firebase tokens, OAuth tokens, or live response dumps.
- Use `GHL_TEST_SUBACCOUNT_PIT` and `GHL_TEST_LOCATION_ID` only as ephemeral environment variables for live QA.
- Generic internal calls require `--experimental`.
- Mutating generic internal calls require `--confirm`.
- Always dry-run internal requests before sending them.
- Do not send customer-facing messages, social posts, invoices, payments, or internal workflow writes unless the user explicitly approves that exact action.

## Common Commands

```bash
./install.sh
./ghl --help
./ghl doctor --json
./ghl endpoints coverage --json
./ghl qa stress --mode mock --json
./ghl qa stress --mode dry-run --json
```

Live read:

```bash
GHL_TEST_SUBACCOUNT_PIT='YOUR_TEST_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_LOCATION_ID='LOCATION_ID' \
./ghl qa stress --mode live-read --json
```

Disposable live write:

```bash
GHL_LIVE_WRITE=1 \
GHL_TEST_SUBACCOUNT_PIT='YOUR_TEST_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_LOCATION_ID='LOCATION_ID' \
./ghl qa stress --mode live-write --json
```

Internal dry-run:

```bash
./ghl --experimental internal request GET '/workflow/{locationId}' \
  --path-param locationId="$GHL_LOCATION_ID" \
  --dry-run \
  --json
```

## Packaging

This repo follows the agent-skills package shape from the Vercel/skills CLI framework:

- `AGENTS.md` is passive always-on agent context for this repository.
- `skills/ghlcli/SKILL.md` is active on-demand context for agents.
- `skills/ghlcli/references/` contains lazily loaded detail.

The npm package exposes:

- `ghlcli`
- `ghl`
- `ghlcli-skill`

`npx ghlcli --help` bootstraps a cached Python venv under `~/.ghlcli/npm-venv/<version>` and forwards to the real Python CLI.

`npx ghlcli-skill install` copies the full skill folder to `~/.codex/skills/ghlcli` unless `CODEX_HOME` or an explicit destination is supplied.

The safest skills CLI discovery check is:

```bash
npx skills add ./ --list
```

The skills CLI install shape is:

```bash
npx skills add ./ --skill ghlcli
npx skills add -g ./ --skill ghlcli -y
```

Depending on the detected agent environment, `npx skills add` may create `.agents/skills/ghlcli`. Keep `.agents/` out of git unless intentionally publishing that installed copy.

## Verification Before Push

```bash
.venv/bin/python -m py_compile cli_anything/gohighlevel/*.py cli_anything/gohighlevel/auth/*.py cli_anything/gohighlevel/adapters/*.py cli_anything/gohighlevel/utils/*.py tests/*.py
.venv/bin/python -m unittest discover -s tests -v
./ghl qa stress --mode dry-run --json
npm pack --dry-run
```
