# Python SDK

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
