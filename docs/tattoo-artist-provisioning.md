# Resumable Tattoo.co artist setup

This operator tool prepares an existing artist's pipeline and tag in master
location `Vh2R6tYeFcaMOFKKSw4a`. Production booking delivery stays in Tattoo.co's
Node worker. The tool never creates contacts/opportunities, sends messages,
updates sales stages, binds an artist, changes flags, or activates delivery.

First review the approved artist inventory and genuine Mia delivery evidence
(TAT-99). Keep new provider provisioning disabled until that evidence and the
current release checks have passed. A proof reference records the operator's
review; it does not query Linear or prove delivery on its own.

Print an offline plan (example artist is illustrative):

```sh
./ghl --json artist-setup plan --artist-id 94 --artist-name 'Example Artist'
```

Read provider state and reconcile using the canonical receipt database:

```sh
./ghl --location-id Vh2R6tYeFcaMOFKKSw4a --json artist-setup run \
  --artist-id 94 --artist-name 'Example Artist'
```

After authorized review, an operator can add `--apply`,
`--confirm-location Vh2R6tYeFcaMOFKKSw4a`, and
`--proof-reference <reviewed-issue-or-receipt>` with
`TAT100_GHL_ROLLOUT_ENABLED=true` in that process's environment. This tool does
not set or change the production flag. Each invocation permits at most one
remote create; `resume_required` means invoke again against the same database.
Both `--apply` and the gate are off by default. Use the existing scoped PIT in
`GHL_API_KEY`; never put credentials into the plan, proof reference, or CLI args.

## Receipts and recovery

The canonical database defaults to `~/.ghlcli/tattoo-artist-setup.sqlite`.
Back it up securely. Use `--state-db` only to select an established coordinated
store or isolated test store. All operators must share the same store and
serialize setup across machines. A copied, deleted, restored-old, or newly
chosen DB loses uncertain-create knowledge: **do not start over with a new DB**.
SQLite compare-and-set prevents competing processes on this store from
claiming the same create. This is not a distributed provider lock.

The plan is immutable for each location/artist. A rename or different stage
layout requires review through the existing admin mapping workflow; it cannot
silently replace a plan. The tool does not edit existing pipelines. A matching
candidate must have exact name, master location, stage names/order, and unique
stage IDs. Case-only collisions, multiple candidates, wrong locations, missing
IDs, malformed/visibly partial lists and changed persisted IDs stop for review.
Persisted IDs are never swapped to a new same-name object.

Before POST, the database commits `creating` with an attempt time. The returned
ID is saved before a separate readback. A crash before POST and a crash after
POST are deliberately treated the same: a missing uncertain object never
permits automatic recreation, including after 403/429/timeout. Later runs read
again and can confirm a unique exact match. There is no reset/recreate command.
No automatic HTTP retry is used; operator-paced read-only reconciliation is
bounded. Provider errors are saved as safe codes, without response bodies.

`verified_for_admin_binding` means pipeline/tag readback succeeded. It is not
complete artist readiness: verify the nineteen field bindings, investigate any
consent/readback discrepancies, deploy reviewed app code, bind paused in admin,
review that artist's legacy writer, record cutoff/cutover, and activate
separately. Genuine new inquiry proof is still required for that artist.

## Provider contracts

Pipeline SDK helpers use the official v3 create/list endpoints already merged
in CLI PR1. Current official tag documentation was retrieved through Context.dev
on September 22, 2026: [Create Tag](https://marketplace.gohighlevel.com/docs/ghl/locations/create-tag),
`POST /locations/:locationId/tags`, Version `v3`, body `{ "name": "..." }`,
response `{ "tag": { "id", "name", "locationId" } }`,
`locations/tags.write` with a sub-account PIT/OAuth token. Actual production
scope and provider writes have not been tested by this development slice.

Tests use fake providers and temporary SQLite only, including crash/restart,
missing uncertain objects, concurrent claim, immutable plan, wrong IDs/location,
pre-existing objects, partial completion and stable readback.
