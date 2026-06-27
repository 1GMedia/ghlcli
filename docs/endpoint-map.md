# Endpoint Coverage Map

Generated from `capabilities.json`, native Click groups, and the open-ghl-mcp endpoint catalog.

## Summary

```json
{
  "categories": 43,
  "endpoints": 576,
  "gateway_only": 29,
  "mcp_only": 2,
  "missing": 0,
  "native": 12
}
```

| Category | Status | Native Group | Endpoints | MCP Tools |
|---|---|---|---:|---|
| `ad-manager` | `gateway-only` |  | 94 | no |
| `affiliate-manager` | `gateway-only` |  | 4 | no |
| `agent-studio` | `gateway-only` |  | 11 | no |
| `associations` | `gateway-only` |  | 10 | no |
| `blogs` | `gateway-only` |  | 7 | no |
| `brand-boards` | `gateway-only` |  | 5 | no |
| `businesses` | `gateway-only` |  | 5 | no |
| `calendars` | `native` | `calendars` | 41 | yes |
| `campaigns` | `gateway-only` |  | 1 | no |
| `companies` | `gateway-only` |  | 1 | no |
| `contacts` | `native` | `contacts` | 32 | yes |
| `conversation-ai` | `gateway-only` |  | 12 | no |
| `conversations` | `native` | `conversations` | 29 | yes |
| `courses` | `gateway-only` |  | 1 | no |
| `custom-fields` | `gateway-only` |  | 8 | yes |
| `custom-menus` | `gateway-only` |  | 5 | no |
| `email-isv` | `gateway-only` |  | 1 | no |
| `emails` | `native` | `emails` | 5 | no |
| `forms` | `native` | `forms` | 3 | yes |
| `funnels` | `gateway-only` |  | 7 | no |
| `gateway` | `mcp-only` |  | 0 | yes |
| `invoices` | `native` | `payments` | 42 | no |
| `knowledge-base` | `gateway-only` |  | 14 | no |
| `links` | `gateway-only` |  | 6 | no |
| `locations` | `native` | `locations` | 29 | no |
| `marketplace` | `gateway-only` |  | 9 | no |
| `medias` | `gateway-only` |  | 7 | no |
| `notes-tasks` | `mcp-only` |  | 0 | yes |
| `oauth` | `native` | `oauth` | 3 | no |
| `objects` | `gateway-only` |  | 9 | no |
| `opportunities` | `native` | `opportunities` | 12 | yes |
| `payments` | `native` | `payments` | 23 | no |
| `phone-system` | `gateway-only` |  | 4 | no |
| `products` | `gateway-only` |  | 27 | no |
| `proposals` | `gateway-only` |  | 4 | no |
| `saas-api` | `gateway-only` |  | 22 | no |
| `snapshots` | `gateway-only` |  | 4 | no |
| `social-media-posting` | `native` | `social` | 40 | no |
| `store` | `gateway-only` |  | 18 | no |
| `surveys` | `gateway-only` |  | 2 | no |
| `users` | `gateway-only` |  | 7 | yes |
| `voice-ai` | `gateway-only` |  | 11 | no |
| `workflows` | `native` | `workflows` | 1 | yes |

## Capability Registry

| Capability | CLI | SDK Helper | Provider | Auth | Mutates | Endpoint |
|---|---|---|---|---|---|---|
| `doctor` | `ghlcli doctor` | `` | `local-diagnostics` | `none` | `False` | `local environment` |
| `capabilities.list` | `ghlcli capabilities list` | `` | `local-registry` | `none` | `False` | `local capabilities.json` |
| `endpoints.list` | `ghlcli endpoints list` | `` | `open-ghl-mcp-specs` | `none` | `False` | `local specs/ghl/*.json` |
| `endpoints.show` | `ghlcli endpoints show` | `` | `open-ghl-mcp-specs` | `none` | `False` | `local specs/ghl/{category}.json` |
| `request` | `ghlcli request` | `GHLClient.request` | `official-public-api` | `pit-or-oauth-location` | `None` | `generic public API request with --path-param support` |
| `internal.request` | `ghl --experimental internal request` | `` | `internal-backend` | `firebase-session` | `None` | `generic backend.leadconnectorhq.com request with --path-param support` |
| `contacts.list` | `ghl contacts list` | `GHLClient.contacts.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /contacts/` |
| `contacts.create` | `ghl contacts create` | `GHLClient.contacts.create` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /contacts/` |
| `opportunities.list` | `ghl opportunities list` | `GHLClient.opportunities.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /opportunities/search` |
| `calendars.book` | `ghl calendars book` | `GHLClient.calendars.book` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /calendars/events/appointments` |
| `workflows.list` | `ghl workflows list` | `GHLClient.workflows.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /workflows/` |
| `workflows.enroll` | `ghl workflows enroll` | `GHLClient.workflows.enroll` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /contacts/{contact_id}/workflow/{workflow_id}` |
| `workflows.remove` | `ghl workflows remove` | `GHLClient.workflows.remove` | `official-public-api` | `pit-or-oauth-location` | `True` | `DELETE /contacts/{contact_id}/workflow/{workflow_id}` |
| `workflows.create` | `ghl --experimental workflows create` | `` | `internal-workflows` | `firebase-session` | `True` | `POST/PUT backend.leadconnectorhq.com/workflow/{location_id}` |
| `workflows.create-step` | `ghl --experimental workflows create-step` | `` | `local-builder` | `none` | `False` | `local JSON file` |
| `workflows.create-n8n` | `ghl --experimental workflows create-n8n` | `` | `internal-workflows` | `firebase-session` | `True` | `POST/PUT backend.leadconnectorhq.com/workflow/{location_id}` |
| `conversations.send` | `ghl conversations send` | `GHLClient.conversations.send` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /conversations/messages` |
| `social.create-post` | `ghl social create-post` | `GHLClient.social.create_post` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /social-media-posting/{location_id}/posts` |
| `locations.search` | `ghl locations search` | `GHLClient.locations.search` | `official-public-api` | `pit-or-oauth-company` | `False` | `GET /locations/search` |
| `oauth.exchange-code` | `ghl oauth exchange-code` | `` | `official-oauth` | `oauth-client-secret` | `False` | `POST /oauth/token` |
| `oauth.location-token` | `ghl oauth location-token` | `` | `official-oauth` | `oauth-company-token` | `False` | `POST /oauth/locationToken` |
| `mcp.servers.list` | `ghl mcp servers list` | `` | `mcp-wrapper` | `none` | `False` | `local upstream inventory` |
| `mcp.tools.list` | `ghl mcp tools list` | `` | `mcp-wrapper` | `none` | `False` | `local MCP source inventory` |
| `contacts.get` | `ghl contacts get` | `GHLClient.contacts.get` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /contacts/{contact_id}` |
| `contacts.update` | `ghl contacts update` | `GHLClient.contacts.update` | `official-public-api` | `pit-or-oauth-location` | `True` | `PUT /contacts/{contact_id}` |
| `contacts.delete` | `ghl contacts delete` | `GHLClient.contacts.delete` | `official-public-api` | `pit-or-oauth-location` | `True` | `DELETE /contacts/{contact_id}` |
| `contacts.search` | `ghl contacts search` | `GHLClient.contacts.search` | `official-public-api` | `pit-or-oauth-location` | `False` | `POST /contacts/search` |
| `contacts.add-tag` | `ghl contacts add-tag` | `GHLClient.contacts.add_tag` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /contacts/{contact_id}/tags` |
| `contacts.remove-tag` | `ghl contacts remove-tag` | `GHLClient.contacts.remove_tag` | `official-public-api` | `pit-or-oauth-location` | `True` | `DELETE /contacts/{contact_id}/tags` |
| `conversations.list` | `ghl conversations list` | `GHLClient.conversations.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /conversations/search` |
| `conversations.get` | `ghl conversations get` | `GHLClient.conversations.get` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /conversations/{conversation_id}` |
| `conversations.messages` | `ghl conversations messages` | `GHLClient.conversations.messages` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /conversations/{conversation_id}/messages` |
| `conversations.get-email` | `ghl conversations get-email` | `GHLClient.conversations.get_email` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /conversations/messages/email/{email_message_id}` |
| `opportunities.get` | `ghl opportunities get` | `GHLClient.opportunities.get` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /opportunities/{opportunity_id}` |
| `opportunities.create` | `ghl opportunities create` | `GHLClient.opportunities.create` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /opportunities/` |
| `opportunities.update` | `ghl opportunities update` | `GHLClient.opportunities.update` | `official-public-api` | `pit-or-oauth-location` | `True` | `PUT /opportunities/{opportunity_id}` |
| `opportunities.delete` | `ghl opportunities delete` | `GHLClient.opportunities.delete` | `official-public-api` | `pit-or-oauth-location` | `True` | `DELETE /opportunities/{opportunity_id}` |
| `opportunities.pipelines` | `ghl opportunities pipelines` | `GHLClient.opportunities.pipelines` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /opportunities/pipelines` |
| `calendars.list` | `ghl calendars list` | `GHLClient.calendars.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /calendars/` |
| `calendars.get` | `ghl calendars get` | `GHLClient.calendars.get` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /calendars/{calendar_id}` |
| `calendars.slots` | `ghl calendars slots` | `GHLClient.calendars.slots` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /calendars/{calendar_id}/free-slots` |
| `calendars.appointments` | `ghl calendars appointments` | `GHLClient.calendars.appointments` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /calendars/events/appointments` |
| `calendars.groups` | `ghl calendars groups` | `GHLClient.calendars.groups` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /calendars/groups` |
| `locations.get` | `ghl locations get` | `GHLClient.locations.get` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /locations/{location_id}` |
| `locations.tags` | `ghl locations tags` | `GHLClient.locations.tags` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /locations/{location_id}/tags` |
| `locations.custom-fields` | `ghl locations custom-fields` | `GHLClient.locations.custom_fields` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /locations/{location_id}/customFields` |
| `locations.custom-values` | `ghl locations custom-values` | `GHLClient.locations.custom_values` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /locations/{location_id}/customValues` |
| `payments.transactions` | `ghl payments transactions` | `GHLClient.payments.transactions` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /payments/transactions` |
| `payments.orders` | `ghl payments orders` | `GHLClient.payments.orders` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /payments/orders` |
| `payments.invoices` | `ghl payments invoices` | `GHLClient.payments.invoices` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /invoices/` |
| `payments.create-invoice` | `ghl payments create-invoice` | `GHLClient.payments.create_invoice` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /invoices/` |
| `forms.list` | `ghl forms list` | `GHLClient.forms.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /forms/` |
| `forms.submissions` | `ghl forms submissions` | `GHLClient.forms.submissions` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /forms/submissions` |
| `social.accounts` | `ghl social accounts` | `GHLClient.social.accounts` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /social-media-posting/{location_id}/accounts` |
| `social.posts` | `ghl social posts` | `GHLClient.social.posts` | `official-public-api` | `pit-or-oauth-location` | `False` | `POST /social-media-posting/{location_id}/posts/list` |
| `documents.list` | `ghl documents list` | `GHLClient.documents.list` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /proposals/document` |
| `documents.templates` | `ghl documents templates` | `GHLClient.documents.templates` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /proposals/templates` |
| `documents.send` | `ghl documents send` | `GHLClient.documents.send` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /proposals/document/send` |
| `documents.send-template` | `ghl documents send-template` | `GHLClient.documents.send_template` | `official-public-api` | `pit-or-oauth-location` | `True` | `POST /proposals/templates/send` |
| `emails.list-campaigns` | `ghl emails list-campaigns` | `GHLClient.emails.list_campaigns` | `official-public-api` | `pit-or-oauth-location` | `False` | `GET /campaigns/` |
