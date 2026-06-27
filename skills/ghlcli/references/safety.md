# ghlcli Safety

## Secrets

- Never commit `.env`, PITs, Firebase tokens, OAuth tokens, or live response dumps.
- Use `GHL_TEST_SUBACCOUNT_PIT` and `GHL_TEST_LOCATION_ID` only as ephemeral environment variables for live QA.
- Do not paste real tokens into docs, reports, test fixtures, or command examples.

## Public API

Public API commands use:

```text
https://services.leadconnectorhq.com
Authorization: Bearer $GHL_API_KEY
```

Use normal public commands first when the public API supports the task.

## Internal API

Internal commands use:

```text
https://backend.leadconnectorhq.com
token-id: <Firebase ID token>
```

Rules:

- Generic internal calls require `--experimental`.
- Mutating generic internal calls require `--confirm`.
- Always run `--dry-run` before sending internal requests.
- Treat internal payloads and paths as unstable because HighLevel can change backend behavior.

## Live QA Boundary

Allowed with `GHL_LIVE_WRITE=1`:

- disposable contacts
- disposable opportunities when pipeline/stage exists
- disposable tags
- cleanup verification

Not allowed without separate explicit approval:

- customer-facing sends
- social posts
- invoices
- payments
- internal workflow writes outside the requested test
