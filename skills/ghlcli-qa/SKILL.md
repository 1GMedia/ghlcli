---
name: ghlcli-qa
description: Use ghlcli QA stress harness, dry-run checks, endpoint coverage reports, secret scans, and packaging validation for safe GoHighLevel CLI development.
---
# ghlcli QA

Default to mock and dry-run checks. Use live credentials only through ephemeral environment variables.

## Local Checks
```bash
.venv/bin/python -m unittest discover -s tests -v
./ghl qa stress --mode mock --json
./ghl qa stress --mode dry-run --json
./ghl endpoints coverage --json
npm pack --dry-run
npx --yes skills add ./ --list
```

## Live Read
```bash
GHL_TEST_SUBACCOUNT_PIT='YOUR_TEST_PRIVATE_INTEGRATION_TOKEN' \
GHL_TEST_LOCATION_ID='LOCATION_ID' \
./ghl qa stress --mode live-read --json
```

## Live Write Boundary
Only run with `GHL_LIVE_WRITE=1`, disposable records, and cleanup verification. Do not test customer-facing sends, social posts, invoices, payments, or internal workflow writes without separate explicit approval.

## Secret Scan
```bash
rg -n "known-token-patterns-here" --hidden -g '!upstreams/**' -g '!.venv/**' -g '!build/**' -g '!.git/**' .
```
