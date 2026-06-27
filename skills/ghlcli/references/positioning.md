# ghlcli Positioning

`ghlcli` combines three lanes:

- **Public/PIT lane**: `services.leadconnectorhq.com` with `Authorization: Bearer $GHL_API_KEY`.
- **Endpoint/spec lane**: open-ghl-mcp catalog discovery plus the public `ghl request` gateway.
- **Firebase/internal lane**: `backend.leadconnectorhq.com` with a Firebase ID token in the `token-id` header.

The Firebase/internal lane gets an ID token from either:

- `GHL_FIREBASE_REFRESH_TOKEN`, preferred, exchanged through Google Secure Token API.
- `GHL_FIREBASE_TOKEN`, direct short-lived token.

Current internal capabilities unlock:

- `ghl --experimental workflows create`
- `ghl --experimental workflows create-n8n`
- workflow folder creation
- workflow draft creation
- tag-trigger creation
- workflow step save/sync
- location tag creation
- builder scripts under `builders/`
- guarded generic backend calls through `ghl --experimental internal request`

Honest claim:

> `ghlcli` combines official public API, MCP/spec endpoint catalog, and an experimental Firebase/internal workflow lane. It does not have more official public endpoints than HighLevel, but it can perform some UI/internal workflow operations that normal public API clients cannot.

Do not claim:

> We can access everything in HighLevel.

The internal client is currently workflow-focused plus a guarded backend gateway. Expand internal endpoint coverage carefully behind `--experimental`, `--dry-run`, redaction, `--confirm` for mutations, and live-safe tests.
