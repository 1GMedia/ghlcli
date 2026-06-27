# ghlcli Command Reference

Generated from the Click command tree. Rebuild with `python scripts/generate_reference_docs.py`.

| Command | Description | Subcommands |
|---|---|---|
| `ghl calendars` | Manage calendars, appointments, and availability slots. | `appointments`, `book`, `get`, `groups`, `list`, `slots` |
| `ghl calendars appointments` | List appointments. |  |
| `ghl calendars book` | Book an appointment. |  |
| `ghl calendars get` | Get calendar details. |  |
| `ghl calendars groups` | List calendar groups. |  |
| `ghl calendars list` | List all calendars. |  |
| `ghl calendars slots` | Get available appointment slots. |  |
| `ghl capabilities` | Inspect the merged ghlcli capability registry. | `list` |
| `ghl capabilities list` | List known and planned capabilities. |  |
| `ghl contacts` | Manage contacts — list, get, create, update, delete, search, tags. | `add-tag`, `create`, `delete`, `get`, `list`, `remove-tag`, `search`, `update` |
| `ghl contacts add-tag` | Add tags to a contact. |  |
| `ghl contacts create` | Create a new contact. |  |
| `ghl contacts delete` | Delete a contact by ID. |  |
| `ghl contacts get` | Get a single contact by ID. |  |
| `ghl contacts list` | List contacts in the location. |  |
| `ghl contacts remove-tag` | Remove tags from a contact. |  |
| `ghl contacts search` | Search contacts with advanced filters. |  |
| `ghl contacts update` | Update a contact by ID. |  |
| `ghl conversations` | Manage conversations and messages. | `get`, `get-email`, `list`, `messages`, `send` |
| `ghl conversations get` | Get conversation details. |  |
| `ghl conversations get-email` | Get full email details (subject, body, headers, attachments).

Two-step workflow: list conversations --type Email → get message IDs → get-email <id>
 |  |
| `ghl conversations list` | List conversations. Use --type Email to see email conversations. |  |
| `ghl conversations messages` | Get messages in a conversation. Use --type Email for email messages only. |  |
| `ghl conversations send` | Send a message in a conversation. |  |
| `ghl doctor` | Check local ghlcli configuration without calling HighLevel. |  |
| `ghl documents` | Documents, contracts, and proposals — list, send, templates. | `list`, `send`, `send-template`, `templates` |
| `ghl documents list` | List documents/contracts. |  |
| `ghl documents send` | Send an existing document to its recipients. |  |
| `ghl documents send-template` | Create and send a contract from a template. |  |
| `ghl documents templates` | List document/contract templates. |  |
| `ghl emails` | Email campaigns and templates. | `list-campaigns` |
| `ghl emails list-campaigns` | List email campaigns. Note: Uses the campaigns API. |  |
| `ghl endpoints` | Inspect the open-ghl-mcp endpoint catalog. | `coverage`, `list`, `search`, `show` |
| `ghl endpoints coverage` | Compare native commands with endpoint catalog coverage. |  |
| `ghl endpoints list` | List endpoint categories or endpoints for a category. |  |
| `ghl endpoints search` | Search endpoint catalog. |  |
| `ghl endpoints show` | Show all endpoints in a category. |  |
| `ghl forms` | Forms and form submissions. | `list`, `submissions` |
| `ghl forms list` | List forms. |  |
| `ghl forms submissions` | Get form submissions. |  |
| `ghl internal` | Experimental internal HighLevel backend gateway. | `request` |
| `ghl internal request` | Call backend.leadconnectorhq.com with Firebase session auth. |  |
| `ghl locations` | Location/sub-account management. | `custom-fields`, `custom-values`, `get`, `search`, `tags` |
| `ghl locations custom-fields` | List custom fields for current location. |  |
| `ghl locations custom-values` | List custom values for current location. |  |
| `ghl locations get` | Get current location details. |  |
| `ghl locations search` | Search locations (requires company-level access). |  |
| `ghl locations tags` | List tags for current location. |  |
| `ghl mcp` | Inspect locally cloned GHL MCP projects. | `servers`, `tools` |
| `ghl mcp servers` | Inspect known local MCP servers. | `list` |
| `ghl mcp servers list` | List known MCP servers and startup commands. |  |
| `ghl mcp tools` | Inspect MCP tools without launching the server. | `list` |
| `ghl mcp tools list` | List tools exposed by a locally cloned MCP server. |  |
| `ghl oauth` | OAuth token helpers. | `exchange-code`, `location-token`, `refresh` |
| `ghl oauth exchange-code` | Exchange an OAuth authorization code for access/refresh tokens. |  |
| `ghl oauth location-token` | Exchange a company token for a location token. |  |
| `ghl oauth refresh` | Refresh an OAuth access token. |  |
| `ghl opportunities` | Manage pipeline opportunities — list, get, create, update, delete. | `create`, `delete`, `get`, `list`, `pipelines`, `update` |
| `ghl opportunities create` | Create a new opportunity. |  |
| `ghl opportunities delete` | Delete an opportunity. |  |
| `ghl opportunities get` | Get opportunity details. |  |
| `ghl opportunities list` | List opportunities. |  |
| `ghl opportunities pipelines` | List all pipelines. |  |
| `ghl opportunities update` | Update an opportunity. |  |
| `ghl payments` | Payments, invoices, transactions, and orders. | `create-invoice`, `invoices`, `orders`, `transactions` |
| `ghl payments create-invoice` | Create a new invoice. |  |
| `ghl payments invoices` | List invoices. |  |
| `ghl payments orders` | List orders. |  |
| `ghl payments transactions` | List transactions. |  |
| `ghl qa` | Run repeatable ghlcli QA and stress checks. | `stress` |
| `ghl qa stress` | Stress-test CLI command wiring, dry-runs, and optional live API reads/writes. |  |
| `ghl repl` | Interactive REPL mode. |  |
| `ghl request` | Call any public HighLevel endpoint configured with PIT/OAuth token. |  |
| `ghl social` | Social media posts and analytics. | `accounts`, `create-post`, `posts` |
| `ghl social accounts` | List connected social media accounts. |  |
| `ghl social create-post` | Create a social media post. |  |
| `ghl social posts` | List social media posts. |  |
| `ghl workflows` | List and manage workflows. Create commands require --experimental. | `create`, `create-n8n`, `create-step`, `enroll`, `list`, `remove` |
| `ghl workflows create` | Create workflows from a campaign JSON file (experimental, internal API).

The JSON file should contain a campaign dict where each key is a workflow
with 'name', 'templates' (linked steps), and optional 'tag' (trigger).
 |  |
| `ghl workflows create-n8n` | Create a minimal GHL workflow that triggers an n8n webhook (experimental).

Creates: [tag trigger] → [webhook POST to n8n URL]
 |  |
| `ghl workflows create-step` | Build a workflow step and append to a JSON file (experimental).

Use repeatedly to build up a workflow step-by-step, then pass the
file to 'workflows create --from-json'.
 |  |
| `ghl workflows enroll` | Enroll a contact in a workflow (public API). |  |
| `ghl workflows list` | List all workflows. |  |
| `ghl workflows remove` | Remove a contact from a workflow (public API). |  |
