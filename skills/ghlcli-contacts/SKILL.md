---
name: ghlcli-contacts
description: Use ghlcli contacts commands and Python SDK helpers for GoHighLevel contact search, create, update, delete, tags, and safe CRM QA. Use when user asks about GHL contacts or contact API endpoints.
---
# ghlcli Contacts

Use the public/PIT lane for contacts. Do not use Firebase/internal APIs for normal contact work.

## Safe Read Commands
```bash
./ghl contacts list --limit 10
./ghl contacts search "name-or-email"
./ghl contacts get <contact_id>
```

## Mutating Commands
```bash
./ghl contacts create --first-name Test --last-name User --email test@example.com
./ghl contacts update <contact_id> --first-name Updated
./ghl contacts add-tag <contact_id> qa-test
./ghl contacts remove-tag <contact_id> qa-test
./ghl contacts delete <contact_id>
```

Use disposable `ghlcli-test-{timestamp}` records for live-write testing.

## Python SDK
```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
client.contacts.list(limit=10)
client.contacts.search(query="test@example.com")
client.contacts.add_tag("contact_id", "qa-test")
```

Primary endpoints: `GET /contacts/`, `GET /contacts/{contact_id}`, `POST /contacts/`, `PUT /contacts/{contact_id}`, `DELETE /contacts/{contact_id}`, `POST /contacts/search`, `POST/DELETE /contacts/{contact_id}/tags`.
