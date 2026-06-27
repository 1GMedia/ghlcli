# ghlcli Packaging

This repo follows the Vercel-style agent skills package shape:

```text
AGENTS.md
skills/
  ghlcli/
    SKILL.md
    references/
      positioning.md
      safety.md
      packaging.md
```

`AGENTS.md` is passive always-on repo context. `skills/ghlcli/SKILL.md` is active, on-demand workflow context. Reference files are loaded only when needed.

## npm Commands

The npm package exposes:

```text
ghlcli
ghl
ghlcli-skill
```

`npx ghlcli --help` bootstraps a cached Python venv under:

```text
~/.ghlcli/npm-venv/<version>
```

`npx ghlcli-skill install` copies the canonical skill folder to:

```text
$CODEX_HOME/skills/ghlcli
```

or:

```text
~/.codex/skills/ghlcli
```

## Vercel Skills CLI

Use this as the safest discovery/validation command:

```bash
npx skills add ./ --list
```

Use these install commands when intentionally installing the skill for supported agent targets:

```bash
npx skills add ./ --skill ghlcli -y
npx skills add -g ./ --skill ghlcli -y
```

Depending on the detected agent environment, the `skills` CLI may create a project-local `.agents/skills/ghlcli` folder. Keep `.agents/` out of git unless intentionally publishing that installed copy.

## Before Publishing

```bash
npm pack --dry-run
./ghl qa stress --mode dry-run --json
npx --yes skills add ./ --list
```
