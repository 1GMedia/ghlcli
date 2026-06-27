# ghlcli

Unofficial GoHighLevel CLI.

A command-line interface for GoHighLevel that lets you (or Claude Code) drive your CRM from the terminal — contacts, opportunities, calendars, conversations, workflows, emails, payments, forms, social media, locations, and documents.

Built by [Lead Gen Jay](https://leadgenjay.com).

---

## What you get

- **15+ command groups** covering core GHL surfaces (contacts, opportunities, calendars, workflows, conversations, emails, payments, forms, social, locations, documents, OAuth, endpoint discovery, MCP inventory, and generic requests).
- **A REPL** — type `ghl` with no args and you get an interactive shell with autocomplete.
- **A Python CLI SDK** — import `GHLClient` and call the same public API surfaces from Python code.
- **Workflow builders** — Python scripts that take a markdown file and turn it into a live GHL workflow (see `builders/`).
- **A one-line token helper** — a DevTools console snippet that exports the Firebase token you need for the "internal" GHL API (the public API can't create workflows; the internal one can). See [`docs/get-firebase-token.md`](docs/get-firebase-token.md).
- **An agent skill package** at `skills/ghlcli/SKILL.md` so Codex, Claude-style agents, and the `skills` CLI can use the CLI safely.

---

## Positioning truth

`ghlcli` combines three lanes:

- **Public/PIT lane**: `services.leadconnectorhq.com` with `Authorization: Bearer $GHL_API_KEY`.
- **Endpoint/spec lane**: open-ghl-mcp catalog discovery plus the public `ghl request` gateway for long-tail official endpoints.
- **Firebase/internal lane**: `backend.leadconnectorhq.com` with a Firebase ID token in the `token-id` header.

The Firebase/internal lane gets the ID token from either `GHL_FIREBASE_REFRESH_TOKEN` (preferred, refreshed through Google Secure Token API) or `GHL_FIREBASE_TOKEN` (direct short-lived token).

Current internal capability unlocks:

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

> `ghlcli` combines the official public API, MCP/spec endpoint catalog, and an experimental Firebase/internal workflow lane. It does not have more official public endpoints than HighLevel, but it can perform some UI/internal workflow operations that normal public API clients cannot.

Do **not** claim:

> We can access everything in HighLevel.

The internal client is currently workflow-focused plus a guarded backend gateway. Expand it carefully behind `--experimental`, `--dry-run`, redaction, and live-safe tests.

---

## CLI SDK

Use `ghlcli` as a command line tool, a Python SDK, or an agent skill package:

```python
from cli_anything.gohighlevel.sdk import GHLClient

client = GHLClient()
contacts = client.contacts.list(limit=10)
result = client.request("GET", "/contacts/", params={"locationId": client.location_id})
```

Reference docs:

- [Command reference](docs/commands.md)
- [Endpoint coverage map](docs/endpoint-map.md)
- [Python SDK](docs/python-sdk.md)
- [Agent skills](docs/agent-skills.md)

Regenerate docs after changing commands, capabilities, or skills:

```bash
python scripts/generate_reference_docs.py
```

---

## Install (60 seconds)

Requirements: **Python 3.10+** and a GoHighLevel sub-account.

```bash
git clone <this repo> gohighlevel-cli
cd gohighlevel-cli
./install.sh
```

The installer creates a `.venv/`, installs the package, and copies `.env.example` → `.env`.

Open `.env` and fill in:

```env
GHL_API_KEY=YOUR_PRIVATE_INTEGRATION_TOKEN  # GHL Settings -> Private Integrations
GHL_LOCATION_ID=YOUR_LOCATION_ID    # the long ID in your GHL URL
```

Smoke test:

```bash
./ghl contacts list --limit 5
```

You should see 5 contacts (or an empty list, depending on the account). Done.

---

## npx and agent skill packaging

This repo is packaged in the Vercel-style agent skills shape:

```text
AGENTS.md
skills/
  ghlcli/
    SKILL.md
    references/
```

Use the Node wrappers locally or through npm/npx:

```bash
node bin/ghlcli.js --help
node bin/ghl.js --help
node bin/ghlcli-skill.js list
```

When published to npm, the command shape is:

```bash
npx ghlcli --help
npx ghl --help
npx ghlcli-skill install
```

Install the skill from this local repo with the skills CLI:

```bash
npx skills add ./ --list
npx skills add ./ --skill ghlcli
npx skills add -g ./ --skill ghlcli -y
```

`ghlcli-skill install` copies the full skill folder to `~/.codex/skills/ghlcli` unless `CODEX_HOME` or an explicit destination is supplied.

Depending on the detected agent environment, `npx skills add` may create `.agents/skills/ghlcli`; keep that generated install copy out of git unless you intentionally want to publish it.

The package is currently marked `"private": true`; flip that only when you are ready for a public npm publish.

---

## QA and stress testing

`ghlcli` includes a reusable QA harness for command wiring, endpoint coverage, and optional live HighLevel checks:

```bash
./ghl endpoints coverage --json
./ghl qa stress --mode mock --json
./ghl qa stress --mode dry-run --json
```

Live QA must use ephemeral environment variables only. Do not paste PITs into repo files or reports:

```bash
GHL_TEST_SUBACCOUNT_PIT='YOUR_TEST_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_LOCATION_ID='LOCATION_ID' \
./ghl qa stress --mode live-read --json
```

Disposable live writes are guarded separately and only create records that have cleanup paths:

```bash
GHL_LIVE_WRITE=1 \
GHL_TEST_SUBACCOUNT_PIT='YOUR_TEST_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_LOCATION_ID='LOCATION_ID' \
./ghl qa stress --mode live-write --json
```

Optional agency preflight:

```bash
GHL_TEST_AGENCY_PIT='YOUR_TEST_AGENCY_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_COMPANY_ID='COMPANY_ID' \
./ghl qa stress --mode live-read --include-agency --json
```

The harness redacts PIT-shaped values in command output and writes markdown reports under `.gstack/qa-reports/`. It does not send customer-facing messages, social posts, invoices, payments, or internal workflow writes.

---

## Quickstart examples

```bash
# Contacts
./ghl contacts search "jay@"
./ghl contacts create --first-name Jay --last-name Test --email jay@test.com
./ghl contacts add-tag <id> consulti_trial

# Workflows
./ghl --json workflows list
./ghl workflows enroll --contact-id <id> --workflow-id <id>

# Opportunities
./ghl opportunities list --pipeline-id <id>

# Conversations
./ghl conversations list --status unread

# REPL (no args = interactive shell with autocomplete)
./ghl
```

`--json` works on most read commands and pipes cleanly into `jq`.

---

## Workflow building (the powerful part)

The public GHL API is read-only for workflows. To **create or update** workflows, the CLI uses GHL's internal API — and that needs a Firebase refresh token.

### Internal backend gateway

Power users can also call internal backend endpoints directly:

```bash
./ghl --experimental internal request GET '/workflow/{locationId}' \
  --path-param locationId="$GHL_LOCATION_ID" \
  --dry-run \
  --json
```

Mutating internal calls require both `--experimental` and `--confirm`:

```bash
./ghl --experimental internal request POST '/workflow/{locationId}' \
  --body request.json \
  --path-param locationId="$GHL_LOCATION_ID" \
  --confirm \
  --json
```

This is not an official public API surface. Treat it as unstable, session-scoped, and only for accounts you control. Always run `--dry-run` first.

### Step 1 — grab the token

Open `app.gohighlevel.com` (logged in), open DevTools (**⌘⌥J** / **Ctrl-Shift-J**), and paste this into the Console:

```js
(async () => {
  const db = await new Promise((res, rej) => {
    const r = indexedDB.open("firebaseLocalStorageDb");
    r.onsuccess = e => res(e.target.result);
    r.onerror = () => rej("Cannot open IndexedDB");
  });
  const entries = await new Promise((res, rej) => {
    const tx = db.transaction("firebaseLocalStorage", "readonly");
    const all = tx.objectStore("firebaseLocalStorage").getAll();
    all.onsuccess = () => res(all.result);
    all.onerror = () => rej("Failed to read store");
  });
  for (const e of entries) {
    const stm = (e?.value || e)?.stsTokenManager;
    if (stm?.refreshToken) {
      copy(stm.refreshToken); // DevTools copy() → clipboard
      console.log("✓ Refresh token copied. Paste into .env as GHL_FIREBASE_REFRESH_TOKEN=");
      return;
    }
  }
  console.warn("No refresh token found — make sure you're logged into GHL.");
})();
```

It copies your refresh token to the clipboard. Paste it into your `.env` as `GHL_FIREBASE_REFRESH_TOKEN=...`. Full walkthrough: [`docs/get-firebase-token.md`](docs/get-firebase-token.md).

### Step 2 — build a workflow

`builders/` has example builders that turn a markdown email-sequence doc into a live workflow:

```bash
# Course Interest sequence (10 emails, 14 days)
python builders/wf1-course-interest-builder.py

# High Ticket Interest sequence (5 emails + 1 SMS)
python builders/wf5-ht-interest-builder.py

# Post-Call Sales (3 tag-triggered branch workflows)
python builders/wf6-post-call-sales-builder.py

# Consulti free-trial nurture (8 emails)
python builders/consulti-nurture-builder.py

# Post-purchase nurture (6 emails)
python builders/post-purchase-nurture-builder.py
```

Each builder supports `--update` to re-deploy without creating a duplicate workflow.

---

## Project layout

```
gohighlevel-cli/
├── ghl                         # the executable wrapper
├── setup.py                    # package definition
├── install.sh                  # one-shot installer
├── .env.example                # template for your secrets
│
├── cli_anything/               # the actual Python package
│   ├── gohighlevel/            # GHL commands (the main thing)
│   │   ├── gohighlevel_cli.py  # ~1,260 lines of CLI
│   │   ├── utils/              # API clients (public + internal + workflow builder)
│   │   └── skills/SKILL.md     # legacy local skill manifest
│   ├── nextcloud/              # bonus: Nextcloud CLI
│   └── blotato/                # bonus: Blotato CLI
│
├── docs/
│   └── get-firebase-token.md   # DevTools snippet for the internal-API token
│
├── skills/
│   └── ghlcli/                 # Vercel-style reusable agent skill
│       ├── SKILL.md
│       └── references/
│
└── builders/                   # example workflow builders
    ├── wf1-course-interest-builder.py
    ├── wf5-ht-interest-builder.py
    ├── wf6-post-call-sales-builder.py
    ├── consulti-nurture-builder.py
    ├── post-purchase-nurture-builder.py
    ├── email-sequences-doc-builder.py
    └── _email_sequences_parser.py
```

---

## Using it with Claude Code

The repo includes a Claude Code skill so Claude can call the CLI on your behalf:

1. Copy `cli_anything/gohighlevel/skills/SKILL.md` into a Claude Code skills directory (e.g. `~/.claude/skills/gohighlevel-cli/SKILL.md`).
2. Add `ghl` to your shell's PATH (or symlink the `ghl` wrapper somewhere on PATH).
3. In any Claude Code session, say "use the gohighlevel-cli skill" and Claude will be able to run `ghl ...` for you.

---

## Two layers of GHL API

The CLI talks to two APIs:

| API | What it can do | How it authenticates |
|-----|----------------|----------------------|
| **Public** (`services.leadconnectorhq.com`) | Read everything, create contacts/opportunities/etc. **Workflows are GET-only here.** | `GHL_API_KEY` (Private Integration Token) |
| **Internal** (`backend.leadconnectorhq.com`) | Experimental workflow builder plus guarded generic backend requests. Hidden behind `--experimental`; mutating generic requests also need `--confirm`. | Firebase JWT, refreshed from `GHL_FIREBASE_REFRESH_TOKEN` |

You only need the Firebase token if you want to **build** workflows. Everything else works with just the API key.

---

## Security notes

- `.env` is gitignored. **Never** commit it.
- The Firebase refresh token is sensitive (it's your full GHL session). Treat it like a password.
- The token-grab snippet only **reads** from your own browser's IndexedDB on the GHL tab and uses the built-in DevTools `copy()` helper — it makes no network calls. See [`docs/get-firebase-token.md`](docs/get-firebase-token.md).

---

## License

Private / personal use.
