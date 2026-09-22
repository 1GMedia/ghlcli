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
- `client.pipelines` (public v3 provisioning)
- `client.calendars`
- `client.locations`
- `client.payments`
- `client.forms`
- `client.social`
- `client.documents`
- `client.emails`

Use `client.request(method, path, body=None, params=None, path_params=None)` for long-tail endpoints.

## Pipeline provisioning

`client.pipelines.list()` and `client.pipelines.create(name=..., stages=[...])`
use the public v3 pipeline API in the client's configured location. Existing
resource helpers retain their configured API version.

```python
pipelines = client.pipelines.list()
# Mutates the configured location; call only when provisioning is authorized.
created = client.pipelines.create(
    name="Tattoo.co — Example Artist [93]",
    stages=["New inquiry", "Contacted", "Qualified", "Consultation/quote", "Booked"],
)
```

Persist the returned pipeline ID against your own immutable artist ID. Contact
identity and opportunity/project identity remain separate. These helpers do not
start workflows, send messages, create contacts, or manage production sync.

Create is not automatically retried. After a timeout, reconcile the location's
pipeline list before another create; pipeline names are unique per location.
Validate the integration's endpoint access in a test location before live use.
A configured token is not proof that v3 provisioning is permitted.

Reference: https://marketplace.gohighlevel.com/docs/ghl/opportunities/create-pipeline
