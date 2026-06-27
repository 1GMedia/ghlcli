---
name: ghlcli-conversations
description: Use ghlcli conversations commands and Python SDK helpers for GoHighLevel conversations, messages, inbound SMS workflows, email details, and safe outbound replies.
---
# ghlcli Conversations

Use the public/PIT lane for conversation reads and message sends. Never send customer-facing messages unless the user explicitly approves the exact action.

## Safe Read Commands
```bash
./ghl conversations list --status unread
./ghl conversations get <conversation_id>
./ghl conversations messages <conversation_id>
./ghl conversations get-email <email_message_id>
```

## Mutating Commands
```bash
./ghl conversations send <conversation_id> --type SMS --message "Approved message"
```

For Hermes/agent-phone style integrations, route inbound events to a bridge first, log the proposed reply, then send only after approval or a configured allowlist.

## Python SDK
```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
client.conversations.list(message_type="SMS")
client.conversations.messages("conversation_id")
client.conversations.send("conversation_id", "Approved reply")
```

Primary endpoints: `GET /conversations/search`, `GET /conversations/{conversation_id}`, `GET /conversations/{conversation_id}/messages`, `POST /conversations/messages`.
