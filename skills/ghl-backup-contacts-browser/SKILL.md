---
name: ghl-backup-contacts-browser
description: Back up every contact from a signed-in GoHighLevel or white-labeled HighLevel contacts page into a verified local Excel workbook using browser UI and accessible DOM state only. Use when the user supplies a HighLevel location or subaccount ID and asks for a manual, browser-based, no-API contact backup with pagination. Never use HighLevel Export or Bulk Export.
---

# Back up HighLevel contacts through the browser

Use the `browser:control-in-app-browser` skill for the signed-in session and the `spreadsheets:Spreadsheets` skill for the final workbook. Read both skills before acting.

## Hard boundaries

- Never click **Export**, use Bulk Export, select all contacts, or start a bulk action.
- Never call a HighLevel, LeadConnector, Firebase, GraphQL, or internal endpoint directly.
- Never inspect cookies, local storage, tokens, authorization headers, or browser profiles.
- Treat this as read-only. Do not add, edit, delete, tag, message, call, or otherwise mutate contacts.
- Save contact data only under an ignored local `outputs/` directory unless the user explicitly approves another destination.

## Inputs and route

Require a location/subaccount ID. Default the white-label host to `app.funnel-design.com` unless the user supplies another HighLevel host.

Open or claim:

```text
https://<host>/v2/location/<locationId>/contacts/smart_list/All
```

Prefer an already signed-in matching tab. If authentication is required, ask the user to sign in in the chosen browser and resume after they confirm.

## Collection workflow

1. Confirm the page heading is **Contacts** and read the dynamic `N Contacts` total.
2. Set the **Page Size** combobox to `100` through the UI. Do not infer that 100 is active.
3. Return to page 1 through **Prev Page**. Do not alter filters or sorting.
4. Import `scripts/collect-contact-backup.mjs` in the browser Node session and call `runContactBackupChunk(...)` repeatedly. Use short chunks so progress can be reported at least once per minute.
5. The collector scrolls the virtualized `.tabulator-tableholder`, reads mounted `.tabulator-row` elements, deduplicates by contact ID, writes one JSON checkpoint per page, and advances only through **Next Page**.
6. Continue until the last UI page. Do not stop after a sample or partial checkpoint.
7. Run `summarizeCheckpoints(outputDir, ["pages", "reconcile"])`. The unique contact count must equal the final dynamic UI total. When the total grows after a refresh, save the refreshed first page with `saveCurrentContactPage(...)` before resuming so newly inserted contacts participate in ID reconciliation. If deletion or larger drift still causes a mismatch, make another page pass into a fresh `pages-pass-N/` directory and reconcile by contact ID. Do not claim completion on a mismatch.
8. Use the bundled spreadsheet runtime and `scripts/build-contact-backup.mjs` to create one `.xlsx` with:
   - `Contacts`: visible HighLevel fields plus Contact ID, detail URL, and source page.
   - `Backup Audit`: location, source route, start/final UI totals, unique rows, pages, timestamps, and a MATCH formula.
9. Inspect formulas and key ranges, scan formula errors, and render both sheets. Stop immediately after the verified workbook is saved.
10. When the user asks for Google Sheets output, import the verified `.xlsx` as a new native Google Sheet using the connected Google Drive/Sheets import capability (`native_google_sheets`). Do not overwrite the local workbook or an existing Sheet. Verify the returned spreadsheet has `Contacts` and `Backup Audit`, the reconciled totals, and `MATCH` status before handing back its URL.

## Browser-session example

```js
var collector = await import("/absolute/path/to/skills/ghl-backup-contacts-browser/scripts/collect-contact-backup.mjs");
var progress = await collector.runContactBackupChunk(ghlTab, {
  outputDir: "/absolute/ignored/outputs/run-id",
  locationId: "LOCATION_ID",
  host: "app.funnel-design.com",
  maxPages: 20,
});
nodeRepl.write(JSON.stringify(progress));
```

Reuse the same browser and tab bindings. Mark the tab as a handoff only when the run must continue in a later turn.

## Workbook command

Load the workspace dependencies, create the required `node_modules` symlink in a writable working directory, and run the spreadsheet operation marker exactly once before authoring. Then run:

```bash
node /absolute/path/to/scripts/build-contact-backup.mjs \
  --input-dir /absolute/path/to/run/pages \
  --extra-input-dir /absolute/path/to/run/reconcile \
  --audit /absolute/path/to/run/progress.json \
  --output /absolute/path/to/run/highlevel-contacts-backup.xlsx
```

The builder fails closed unless its unique rows equal the audit total.

## End-to-end handoff checklist

- Source: signed-in white-label HighLevel UI at the supplied location/subaccount route.
- Collection: visible UI/accessible DOM only; page size 100; all pages; checkpointed and resumable.
- Reconciliation: unique Contact IDs equal the latest dynamic UI total.
- Local artifact: verified `.xlsx` with `Contacts` and `Backup Audit` sheets and no formula errors.
- Optional cloud artifact: a new native Google Sheet converted from that verified workbook, with both tabs and MATCH audit preserved.
- Prohibited throughout: Export, Bulk Export, bulk actions, direct API/internal calls, cookie/token/storage inspection, and contact mutations.
