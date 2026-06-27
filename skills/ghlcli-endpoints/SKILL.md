---
name: ghlcli-endpoints
description: Use ghlcli endpoint discovery, coverage, capabilities, and generic request gateway for long-tail GoHighLevel API endpoints not yet wrapped as native commands.
---
# ghlcli Endpoints

Use this skill when the user needs endpoint discovery, API parity checks, or a long-tail HighLevel API call.

## Discovery
```bash
./ghl endpoints list --json
./ghl endpoints search "invoice" --json
./ghl endpoints show contacts --json
./ghl endpoints coverage --json
./ghl capabilities list --merged --json
```

## Generic Public Gateway
```bash
./ghl request GET /contacts/ --dry-run --json
./ghl request POST /contacts/ --body body.json --dry-run --json
```

Remove `--dry-run` only after checking method, path, query params, auth lane, and mutation risk.

## Python SDK
```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
client.request("GET", "/contacts/", params={"locationId": client.location_id})
```

Endpoint coverage comes from the open-ghl-mcp spec catalog when available; native commands and SDK helpers are mapped through `capabilities.json`.
