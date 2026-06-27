---
name: ghlcli-workflows
description: Use ghlcli workflow commands and Python SDK helpers for official workflow list/enroll/remove plus guarded experimental Firebase/internal workflow creation.
---
# ghlcli Workflows

Keep workflow lanes separate.

## Official Public Lane
```bash
./ghl workflows list
./ghl workflows enroll --contact-id <contact_id> --workflow-id <workflow_id>
./ghl workflows remove --contact-id <contact_id> --workflow-id <workflow_id>
```

Python SDK:
```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
client.workflows.list()
client.workflows.enroll("contact_id", "workflow_id")
```

## Experimental Internal Lane
```bash
./ghl --experimental workflows create --name "Workflow" --json-file workflow.json
./ghl --experimental workflows create-n8n --name "Webhook workflow" --webhook-url https://example.com/hook
./ghl --experimental internal request GET '/workflow/{locationId}' --dry-run --json
```

Internal workflow creation uses Firebase session auth and must stay behind `--experimental`, dry-run, redaction, and explicit user approval for live writes.
