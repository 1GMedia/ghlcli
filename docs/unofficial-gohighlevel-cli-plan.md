# ghlcli Plan

Goal: turn `ghlcli` into a single unofficial GoHighLevel/LeadConnector CLI that can absorb useful GHL API, MCP, and LCI projects even when they are written in different languages.

## Product Shape

The CLI should expose one coherent command surface:

```bash
ghl contacts ...
ghl workflows ...
ghl conversations ...
ghl social ...
ghl oauth ...
ghl mcp ...
ghl integrations ...
```

Internally, commands can be backed by multiple adapters:

```text
official-public-api      services.leadconnectorhq.com, PIT or OAuth token
official-oauth           /oauth/token and location-token exchange
internal-workflows       backend.leadconnectorhq.com, Firebase browser token
mcp-wrapper              local/remote MCP server tools
legacy-subprocess        Node/Go/Python/etc project wrapped as a command
native-port              rewritten Python implementation
```

The user-facing CLI should hide that mess behind stable commands, while still making auth and risk visible.

## Positioning Truth

`ghlcli` is not trying to have more official public endpoints than HighLevel itself. The winning claim is broader and more precise:

> `ghlcli` combines the official public API, MCP/spec endpoint catalog, and an experimental Firebase/internal workflow lane. It does not have more official public endpoints than HighLevel, but it can perform some UI/internal workflow operations that normal public API clients cannot.

Three auth/adapter lanes define the product:

- **Public/PIT lane**: `services.leadconnectorhq.com` with `Authorization: Bearer $GHL_API_KEY`.
- **Endpoint/spec lane**: open-ghl-mcp catalog discovery plus the public `ghl request` gateway.
- **Firebase/internal lane**: `backend.leadconnectorhq.com` with a Firebase ID token in `token-id`.

The Firebase ID token comes from `GHL_FIREBASE_REFRESH_TOKEN` (preferred, exchanged through Google Secure Token API) or `GHL_FIREBASE_TOKEN` (direct short-lived token).

Current internal unlocks:

- `ghl --experimental workflows create`
- `ghl --experimental workflows create-n8n`
- workflow folder creation
- workflow draft creation
- tag-trigger creation
- workflow step save/sync
- location tag creation
- builder scripts under `builders/`
- guarded generic backend calls through `ghl --experimental internal request`

Do not claim "we can access everything in HighLevel." The internal client is currently workflow-focused plus a guarded backend gateway. Any expansion into more internal UI endpoints must stay behind `--experimental`, `--dry-run`, redaction, `--confirm` for mutations, and live-safe tests.

## Core Rule

Do not merge every project as random commands.

Create a capability layer. Each capability declares:

```json
{
  "name": "workflows.create",
  "provider": "internal-workflows",
  "auth": "firebase-session",
  "stability": "experimental",
  "mutates": true,
  "command": "ghl --experimental workflows create"
}
```

That lets Codex, humans, and scripts know whether a command is official, mutating, experimental, OAuth-only, or powered by a wrapped MCP/LCI project.

## Auth Lanes

### Private Integration Token

Best for personal/internal use against known locations.

```env
GHL_API_KEY=YOUR_PRIVATE_INTEGRATION_TOKEN
GHL_LOCATION_ID=...
```

### OAuth App

Best for Marketplace/app-style multi-location installs.

Required future CLI commands:

```bash
ghl oauth authorize-url
ghl oauth exchange-code
ghl oauth refresh
ghl oauth location-token
ghl oauth installs list
```

### Firebase Session

Only for experimental internal workflow-builder features.

```env
GHL_FIREBASE_REFRESH_TOKEN=...
```

Must stay behind `--experimental` and clearly say it is not official API behavior.

This lane is intentionally retained. The CLI should keep the Firebase/internal
workflow builder path as a power-user feature even as official PIT and OAuth
support improves. Treat it as a protected adapter with extra warnings, not as
temporary code to delete.

## Adapter Strategy

### 1. Native Python

Use for stable public API operations:

```text
contacts
opportunities
calendars
conversations
payments
forms
locations
social posting
workflow list/enroll/remove
```

### 2. Subprocess Wrapper

Use for useful external projects before porting them.

Example:

```bash
ghl integrations run some-node-tool -- --arg value
```

Implementation can call:

```python
subprocess.run(["node", "..."], check=True)
```

### 3. MCP Adapter

Use for existing GHL MCP servers.

Desired commands:

```bash
ghl mcp servers list
ghl mcp tools list <server>
ghl mcp call <server> <tool> --json-args args.json
```

This makes MCP tools available from terminal workflows and lets Codex use one CLI regardless of the original MCP implementation language.

### 4. Native Port Later

Once a wrapped project proves useful, port the high-value endpoints into Python and retire the wrapper.

## Proposed Package Layout

```text
cli_anything/gohighlevel/
  cli.py
  registry.py
  capabilities.json
  auth/
    pit.py
    oauth.py
    firebase.py
  adapters/
    public_api.py
    internal_workflows.py
    mcp.py
    subprocess_tool.py
  commands/
    contacts.py
    workflows.py
    conversations.py
    social.py
    oauth.py
    mcp.py
  utils/
```

Current repo can migrate gradually from the single large `gohighlevel_cli.py`.

## Workflow Feature Boundary

Official/public style:

```bash
ghl workflows list
ghl workflows enroll --contact-id ... --workflow-id ...
ghl workflows remove --contact-id ... --workflow-id ...
```

Internal experimental style:

```bash
ghl --experimental workflows create ...
ghl --experimental workflows create-n8n ...
```

The internal path can create folders, workflows, triggers, steps, and canvas metadata by using GHL web-app backend endpoints. Keep it isolated.

Power-user internal gateway:

```bash
ghl --experimental internal request GET /workflow/{locationId} --path-param locationId=...
ghl --experimental internal request POST /workflow/{locationId} --body request.json --confirm
```

This is a protected escape hatch, not a public API replacement. It must stay behind `--experimental`, mutating calls require `--confirm`, and docs/tests should treat payloads as unstable.

## MVP Milestones

### M1: Stabilize Current CLI

- Keep `./ghl` runnable from repo root.
- Remove hard-coded default location ID.
- Add `ghl doctor` for env/auth checks.
- Add `ghl capabilities list`.
- Add `--dry-run` to all mutating commands where practical.
- Normalize command output with `--json`.

### M2: Auth Manager

- Add PIT profile support.
- Add OAuth token storage and refresh.
- Add location-token exchange.
- Add safe redaction in all diagnostics.

### M3: Capability Registry

- Create `capabilities.json`.
- Mark commands as read/write, official/internal, auth type, and adapter.
- Use registry in `ghl doctor`, Codex skill docs, and help output.

### M4: MCP Ingestion

- Inventory known GHL MCP/LCI projects.
- Wrap each as subprocess/MCP adapter first.
- Add `ghl mcp tools list` and `ghl mcp call`.
- Promote stable tools into native Python commands.

### M5: Workflow Power Tools

- Keep existing internal workflow builder.
- Add schema examples for workflow JSON.
- Add validate-only mode.
- Add import/export:

```bash
ghl workflows export --workflow-id ...
ghl workflows validate --from-json ...
ghl --experimental workflows create --from-json ...
```

### M6: Distribution

- Rename package to an intentional project name.
- Add test suite with mocked HTTP.
- Add release command/install docs.
- Add shell completions.

### M7: QA Trust Layer

- Use `ghl endpoints coverage` to compare native command groups against the open-ghl-mcp endpoint catalog.
- Use `ghl qa stress --mode mock|dry-run|live-read|live-write` before expanding native commands.
- Keep live tokens env-only via `GHL_TEST_SUBACCOUNT_PIT`, `GHL_TEST_LOCATION_ID`, optional `GHL_TEST_AGENCY_PIT`, and optional `GHL_TEST_COMPANY_ID`.
- Require `GHL_LIVE_WRITE=1` for disposable write tests.
- Keep live-write scope to cleanup-safe CRM records; no customer sends, social posts, invoices, payments, or internal workflow writes without separate approval.
- Write repeatable QA reports under `.gstack/qa-reports/` so command expansion is guided by evidence instead of guesses.

## Naming Options

Working names:

```text
ghlcli
ghl-unofficial
highlevel-cli
leadconnector-cli
ghlx
hlctl
```

`ghl` is the best command alias, even if the package name is longer.

## Safety Rules

- Never print tokens.
- Never run mutating commands without explicit user intent.
- All internal/Firebase features require `--experimental`.
- All wrapped third-party tools declare their source path and runtime.
- Every command should be traceable to a provider and auth lane.

## First Implementation Slice

1. Add `ghl doctor`.
2. Add `capabilities.json` for current commands.
3. Add `ghl capabilities list`.
4. Split auth helpers out of `utils/ghl_client.py`.
5. Add OAuth client skeleton.
6. Inventory external GHL MCP/LCI repos and wrap one as proof.
