# Agent Skills

Generated from `skills/ghlcli*` skill folders.

| Skill | Purpose |
|---|---|
| `ghlcli` | Use unofficial GoHighLevel CLI for public API commands, endpoint/spec discovery, QA stress testing, protected Firebase/internal workflow tooling. Use when user mentions ghlcli, GoHighLevel CLI, LeadConnector CLI, GHL workflows, GHL contacts, HighLevel MCP, packaging CLI agent skill. |
| `ghlcli-contacts` | Use ghlcli contacts commands and Python SDK helpers for GoHighLevel contact search, create, update, delete, tags, and safe CRM QA. Use when user asks about GHL contacts or contact API endpoints. |
| `ghlcli-conversations` | Use ghlcli conversations commands and Python SDK helpers for GoHighLevel conversations, messages, inbound SMS workflows, email details, and safe outbound replies. |
| `ghlcli-endpoints` | Use ghlcli endpoint discovery, coverage, capabilities, and generic request gateway for long-tail GoHighLevel API endpoints not yet wrapped as native commands. |
| `ghlcli-qa` | Use ghlcli QA stress harness, dry-run checks, endpoint coverage reports, secret scans, and packaging validation for safe GoHighLevel CLI development. |
| `ghlcli-workflows` | Use ghlcli workflow commands and Python SDK helpers for official workflow list/enroll/remove plus guarded experimental Firebase/internal workflow creation. |

Install/discover locally:

```bash
npx --yes skills add ./ --list
npx --yes skills add ./ --skill ghlcli -y
```
