#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SOURCE = path.join(ROOT, "skills", "ghlcli");

function usage() {
  console.log(`ghlcli-skill

Usage:
  ghlcli-skill path
  ghlcli-skill cat
  ghlcli-skill list
  ghlcli-skill install [destination]

Default destination:
  $CODEX_HOME/skills/ghlcli
  or ~/.codex/skills/ghlcli
`);
}

function defaultDestination() {
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  return path.join(codexHome, "skills", "ghlcli");
}

function copyDirectory(source, target) {
  fs.mkdirSync(target, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    const from = path.join(source, entry.name);
    const to = path.join(target, entry.name);
    if (entry.isDirectory()) {
      copyDirectory(from, to);
    } else if (entry.isFile()) {
      fs.copyFileSync(from, to);
    }
  }
}

function listFiles(dir, prefix = "") {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  for (const entry of entries) {
    const relative = path.join(prefix, entry.name);
    const fullPath = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      listFiles(fullPath, relative);
    } else if (entry.isFile()) {
      console.log(relative);
    }
  }
}

function resolveDestination(destination) {
  const target = path.resolve(destination || defaultDestination());
  if (target.endsWith("SKILL.md")) {
    return path.dirname(target);
  }
  return target;
}

const [command, destination] = process.argv.slice(2);

if (!command || command === "path") {
  console.log(SOURCE);
} else if (command === "cat") {
  process.stdout.write(fs.readFileSync(path.join(SOURCE, "SKILL.md"), "utf8"));
} else if (command === "list") {
  listFiles(SOURCE);
} else if (command === "install") {
  const target = resolveDestination(destination);
  copyDirectory(SOURCE, target);
  console.log(target);
} else if (command === "--help" || command === "-h" || command === "help") {
  usage();
} else {
  console.error(`Unknown command: ${command}`);
  usage();
  process.exit(1);
}
