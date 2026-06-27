# Upstream Ingestion Batch 001

This batch records the first external projects to mine for `ghlcli`.

The repos are cloned locally under ignored `upstreams/` for analysis only.

## Snapshot

| Project | Language | Local Path | HEAD | Primary Use |
| --- | --- | --- | --- | --- |
| `basicmachines-co/open-ghl-mcp` | Python | `upstreams/open-ghl-mcp` | `1b92e43a13c27b53bc073f94fd407080bfbe8397` | MCP server, OAuth/location token handling, endpoint specs, full-surface gateway |
| `MusheAbdulHakim/gohighlevel-php-sdk` | PHP | `upstreams/gohighlevel-php-sdk` | `b345ed51a06f94caa30456da829f589827a41e50` | Broad typed resource SDK coverage |
| `checkoutjoy/gohighlevel-go` | Go | `upstreams/gohighlevel-go` | `920b7081863d9433912333227e1a888ff4964b00` | Clean OAuth/token refresh and contacts SDK pattern |

## basicmachines-co/open-ghl-mcp

Best role in `ghlcli`: MCP adapter plus official endpoint/spec source.

Notable findings:

- Python MCP server.
- OAuth 2.0 setup with agency/company token and automatic location-token exchange.
- Curated tools for contacts, conversations, opportunities, calendars, forms, custom fields/values, notes/tasks, users, workflows.
- Gateway tools: `ghl_list_endpoints` and `ghl_request`.
- Large OpenAPI-style specs under `specs/ghl/`.
- Social media posting spec has 29 paths, far beyond current `ghl social` coverage.
- Public workflow spec only lists `GET /workflows/`, confirming that full workflow creation still belongs in our internal Firebase lane.

Port targets:

- OAuth setup and location-token exchange.
- Endpoint catalog search/list.
- Generic request gateway.
- Mutating-command confirmation gates.
- Notes/tasks, users, custom fields/values.
- Social planner OAuth/account/post expansion.

Likely CLI shape:

```bash
ghlcli mcp servers list
ghlcli mcp tools list open-ghl-mcp
ghlcli endpoints list --category social-media-posting
ghlcli request GET /contacts --location-id ...
```

## MusheAbdulHakim/gohighlevel-php-sdk

Best role in `ghlcli`: broad resource checklist and payload-shape reference.

Notable findings:

- PHP 8.2+ SDK.
- PSR-18/PSR-4 package.
- OAuth helper examples.
- Resource folders cover:
  - businesses
  - calendars
  - campaigns
  - companies
  - contacts
  - conversations
  - courses
  - forms
  - funnels
  - invoices
  - trigger links
  - locations
  - media library
  - opportunities
  - payments
  - products
  - SaaS
  - snapshots
  - social planner Google
  - surveys
  - users
  - workflows

Port targets:

- Media library commands.
- Trigger links.
- Products/prices.
- Surveys.
- Snapshots.
- Funnel redirects.
- Payment provider/config surfaces.
- Rich contact subresources: notes, tasks, followers, campaigns, workflows.

Likely CLI shape:

```bash
ghlcli media upload ...
ghlcli trigger-links list ...
ghlcli products list ...
ghlcli snapshots list ...
```

## checkoutjoy/gohighlevel-go

Best role in `ghlcli`: auth/client architecture reference.

Notable findings:

- Go SDK.
- Smaller current source footprint.
- Strong OAuth/token-refresh design:
  - access-token-only mode
  - authorization-code exchange
  - refresh-token exchange
  - automatic refresh on 401
  - callback for storing refreshed tokens
- Contact client includes create, get, update, delete, upsert, and list patterns.

Port targets:

- Python OAuth client shape.
- Token refresh callback/storage pattern.
- Contact request/response schema sanity checks.
- Retry-on-401 behavior.

Likely CLI shape:

```bash
ghlcli oauth exchange-code ...
ghlcli oauth refresh ...
ghlcli contacts upsert ...
```

## Current Coverage Gap Examples

`open-ghl-mcp` specs show these categories where `ghlcli` can grow:

```text
ad-manager
affiliate-manager
agent-studio
associations
blogs
brand-boards
businesses
courses
custom-menus
email-isv
funnels
knowledge-base
links
marketplace
medias
objects
phone-system
products
saas-api
snapshots
store
surveys
users
voice-ai
```

## Decision

Keep `ghlcli` Python-first.

Use upstreams in this order:

1. Wrap or mine `open-ghl-mcp` for OAuth, specs, gateway, and MCP bridge.
2. Use PHP SDK docs/classes as a broad coverage checklist.
3. Port the Go SDK OAuth refresh pattern into native Python.
4. Keep Firebase/internal workflow builder as a protected experimental adapter.

Do not vendor upstream source into the package yet. Keep local clones ignored under `upstreams/` and port deliberately.
