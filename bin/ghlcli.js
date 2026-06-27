#!/usr/bin/env node
"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const PKG = require(path.join(ROOT, "package.json"));
const VENV_ROOT =
  process.env.GHLCLI_NPX_VENV ||
  path.join(os.homedir(), ".ghlcli", "npm-venv", PKG.version);
const SENTINEL = path.join(VENV_ROOT, ".ghlcli-installed");
const LOCK_FILE = path.join(VENV_ROOT, ".ghlcli-install.lock");

function run(command, args, options = {}) {
  const result = childProcess.spawnSync(command, args, {
    stdio: options.stdio || "inherit",
    env: process.env,
    cwd: ROOT,
  });
  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    process.exit(result.status || 1);
  }
  return result;
}

function capture(command, args) {
  const result = childProcess.spawnSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (result.status !== 0 || result.error) {
    return null;
  }
  return (result.stdout || "").trim();
}

function pythonCandidates() {
  return [process.env.PYTHON, "python3", "python"].filter(Boolean);
}

function findPython() {
  for (const candidate of pythonCandidates()) {
    const version = capture(candidate, [
      "-c",
      "import sys; print('%d.%d' % sys.version_info[:2])",
    ]);
    if (!version) {
      continue;
    }
    const [major, minor] = version.split(".").map(Number);
    if (major > 3 || (major === 3 && minor >= 10)) {
      return candidate;
    }
  }
  console.error("ghlcli requires Python 3.10+ on PATH. Set PYTHON=/path/to/python if needed.");
  process.exit(1);
}

function venvPython() {
  return process.platform === "win32"
    ? path.join(VENV_ROOT, "Scripts", "python.exe")
    : path.join(VENV_ROOT, "bin", "python");
}

function venvGhlcli() {
  return process.platform === "win32"
    ? path.join(VENV_ROOT, "Scripts", "ghlcli.exe")
    : path.join(VENV_ROOT, "bin", "ghlcli");
}

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

function withInstallLock(callback) {
  fs.mkdirSync(VENV_ROOT, { recursive: true });
  const started = Date.now();
  while (true) {
    try {
      const fd = fs.openSync(LOCK_FILE, "wx");
      try {
        return callback();
      } finally {
        fs.closeSync(fd);
        fs.rmSync(LOCK_FILE, { force: true });
      }
    } catch (error) {
      if (error.code !== "EEXIST") {
        throw error;
      }
      if (Date.now() - started > 10 * 60 * 1000) {
        console.error(`ghlcli: timed out waiting for install lock at ${LOCK_FILE}`);
        process.exit(1);
      }
      sleep(500);
      if (fs.existsSync(SENTINEL)) {
        return undefined;
      }
    }
  }
}

function ensureVenv() {
  if (fs.existsSync(SENTINEL)) {
    return;
  }
  withInstallLock(() => {
    if (fs.existsSync(SENTINEL)) {
      return;
    }
    const py = findPython();
    if (!fs.existsSync(venvPython())) {
      console.error(`ghlcli: creating Python environment at ${VENV_ROOT}`);
      run(py, ["-m", "venv", VENV_ROOT]);
    }

    console.error("ghlcli: installing Python package into cached environment");
    run(venvPython(), ["-m", "pip", "install", "--upgrade", "pip"], { stdio: "ignore" });
    run(venvPython(), ["-m", "pip", "install", ROOT], { stdio: "ignore" });
    fs.writeFileSync(SENTINEL, `${PKG.name}@${PKG.version}\n`);
  });
}

function main() {
  ensureVenv();
  const args = process.argv.slice(2);
  const result = childProcess.spawnSync(venvGhlcli(), args, {
    stdio: "inherit",
    env: process.env,
    cwd: process.cwd(),
  });
  if (result.error) {
    console.error(`ghlcli: failed to launch Python CLI: ${result.error.message}`);
    process.exit(1);
  }
  process.exit(result.status || 0);
}

main();
