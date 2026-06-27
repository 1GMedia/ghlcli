---
name: "ghlcli"
description: "Use the local unofficial GoHighLevel CLI for contacts, opportunities, calendars, workflows, conversations, documents, payments, forms, social posts, and locations."
triggers:
  - gohighlevel
  - ghl cli
  - ghl contacts
  - ghl workflows
  - highlevel cli
---

# ghlcli

Use this skill when the user asks Codex to operate or inspect the local GoHighLevel CLI in:

```bash
/Users/gavinbasuel/Documents/GHL CLI
```

## Setup

The project is installed with a repo-local virtualenv:

```bash
cd "/Users/gavinbasuel/Documents/GHL CLI"
./install.sh
```

Run commands through the wrapper so `.venv` and `.env` are loaded:

```bash
./ghl --help
./ghl doctor --json
./ghl capabilities list --json
./ghl endpoints list --json
./ghl endpoints coverage --json
./ghl qa stress --mode dry-run --json
./ghl --json contacts list --limit 10
```

Required `.env` values for public API commands:

```env
GHL_API_KEY=...
GHL_LOCATION_ID=...
```

Optional `.env` values for experimental internal workflow create/update commands:

```env
GHL_FIREBASE_REFRESH_TOKEN=...
GHL_FIREBASE_TOKEN=...
```

Prefer `GHL_FIREBASE_REFRESH_TOKEN`; see `docs/get-firebase-token.md`.

## Positioning Truth

`ghlcli` combines three lanes:

- Public/PIT lane: `services.leadconnectorhq.com` with `Authorization: Bearer $GHL_API_KEY`.
- Endpoint/spec lane: open-ghl-mcp catalog discovery plus public `ghl request` gateway.
- Firebase/internal lane: `backend.leadconnectorhq.com` with Firebase ID token in `token-id` header.

Firebase ID token source is either `GHL_FIREBASE_REFRESH_TOKEN` (preferred, refreshed through Google Secure Token API) or `GHL_FIREBASE_TOKEN` (direct short-lived token).

Current internal capability unlocks workflow creation, workflow folder creation, workflow draft creation, tag-trigger creation, workflow step save/sync, location tag creation, builder scripts under `builders/`, and guarded generic backend calls via `ghl --experimental internal request`.

Honest claim: `ghlcli` combines the official public API, MCP/spec endpoint catalog, and an experimental Firebase/internal workflow lane. It does not have more official public endpoints than HighLevel, but it can perform some UI/internal workflow operations that normal public API clients cannot.

Do not claim: "We can access everything in HighLevel." The internal client is currently workflow-focused plus a guarded backend gateway.

## Command Groups

Global flags:

```bash
./ghl --json
./ghl --location-id <location_id>
./ghl --experimental
```

Public API commands:

```bash
./ghl doctor
./ghl capabilities list
./ghl endpoints list|show|search|coverage
./ghl request <METHOD> <PATH> [--path-param key=value]
./ghl --experimental internal request <METHOD> <PATH> [--path-param key=value] [--dry-run]
./ghl qa stress --mode mock|dry-run|live-read|live-write
./ghl contacts list|get|create|update|delete|search|add-tag|remove-tag
./ghl opportunities list|get|create|update|delete|pipelines
./ghl calendars list|get|slots|appointments|book|groups
./ghl workflows list|enroll|remove
./ghl documents list|templates|send|send-template
./ghl conversations list|get|messages|get-email|send
./ghl emails list-campaigns
./ghl payments transactions|orders|invoices|create-invoice
./ghl forms list|submissions
./ghl social accounts|posts|create-post
./ghl locations get|search|tags|custom-fields|custom-values
./ghl oauth exchange-code|refresh|location-token
./ghl mcp servers list
./ghl mcp tools list
```

Experimental workflow-builder commands:

```bash
./ghl --experimental workflows create --name <name> --from-json <campaign.json> [--folder <folder>]
./ghl --experimental workflows create-step --type email|sms|wait|tag|webhook|ai --name <name> --output-file <steps.json>
./ghl --experimental workflows create-n8n --name <name> --webhook-url <url> [--tag <tag>] [--folder <folder>]
./ghl --experimental internal request GET '/workflow/{locationId}' --path-param locationId=<location_id> --dry-run --json
```

## Workflow Auth Boundary

`workflows list`, `workflows enroll`, and `workflows remove` use the public API at:

```text
https://services.leadconnectorhq.com
Authorization: Bearer $GHL_API_KEY
```

`workflows create` and `workflows create-n8n` use the internal backend at:

```text
https://backend.leadconnectorhq.com
token-id: <Firebase ID token>
```

`internal request` is a generic backend gateway for power users. Mutating internal calls require `--confirm`. Always dry-run first.

Treat the internal workflow path as unstable and sensitive. It depends on a logged-in GHL browser session token and may break if HighLevel changes internal endpoints or payloads.

## QA Harness

Use env-only test credentials for live stress runs:

```bash
GHL_TEST_SUBACCOUNT_PIT=...
GHL_TEST_LOCATION_ID=...
GHL_TEST_AGENCY_PIT=...      # optional
GHL_TEST_COMPANY_ID=...      # optional
GHL_LIVE_WRITE=1             # required only for live-write
```

Never store test PITs in repo files. `qa stress` redacts PIT-shaped values and writes reports under `.gstack/qa-reports/`. Live-write scope is disposable contacts/opportunities/tags only; no customer sends, social posts, invoices, payments, or internal workflow writes.

## Agent Notes

- Use `--json` for machine-readable output.
- Never print `.env` or token values.
- Do not run mutating commands unless the user explicitly asks.
- For live workflow creation, confirm the target `GHL_LOCATION_ID`, workflow name, and whether `--experimental` is intended.
- Prefer read-only smoke tests first: `./ghl --help`, `./ghl workflows --help`, `./ghl --json workflows list`, `./ghl qa stress --mode dry-run --json`.
