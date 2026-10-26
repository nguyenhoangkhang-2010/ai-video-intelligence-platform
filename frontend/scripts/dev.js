#!/usr/bin/env node
/**
 * Single-instance dev server launcher for `npm run dev`.
 *
 * Root cause this exists for: `next dev` with no explicit port falls
 * back silently (3000 -> 3001 -> 3002 -> ...) whenever the port it
 * wants is taken - see node_modules/next/dist/cli/next-dev.js
 * ("If neither --port nor PORT were specified, it's okay to retry new
 * ports.") and node_modules/next/dist/server/lib/start-server.js
 * (`allowRetry && ... EADDRINUSE`). That's true even when the thing
 * "taking" the port is a second `npm run dev` of this exact project
 * forgotten in another terminal - Next has no concept of "is this
 * already me".
 *
 * Fix has two layers:
 *   1. Always pass an explicit port (-p 3000) so Next's own
 *      `allowRetry` is false - it will refuse to silently move to
 *      another port no matter what, with or without this script.
 *   2. Before even spawning Next, check what (if anything) already
 *      owns port 3000, so a second `npm run dev` of this same project
 *      exits cleanly instead of crashing on a raw EADDRINUSE, and a
 *      port genuinely held by something else fails with an actionable
 *      message instead of Next's generic stack trace.
 *
 * Detection is project-scoped, not "any node process": it reads the
 * actual command line of whatever process owns the port and checks it
 * contains this project's own frontend directory - never killed,
 * never guessed, never matched on process name alone (that would risk
 * misidentifying an unrelated Node process as this one).
 */
"use strict";

const { spawn, spawnSync } = require("node:child_process");
const path = require("node:path");

const PORT = 3000;
const FRONTEND_DIR = path.resolve(__dirname, "..");
const IS_WINDOWS = process.platform === "win32";

/** PID of whatever is listening on `port`, or null if nothing is / detection failed. */
function findListenerPid(port) {
  if (IS_WINDOWS) {
    const result = spawnSync("netstat", ["-ano"], { encoding: "utf8" });
    if (result.status !== 0 || !result.stdout) return null;

    const line = result.stdout
      .split("\n")
      .find((row) => new RegExp(`:${port}\\s`).test(row) && /LISTENING/i.test(row));
    if (!line) return null;

    const columns = line.trim().split(/\s+/);
    const pid = columns[columns.length - 1];
    return /^\d+$/.test(pid) ? pid : null;
  }

  const result = spawnSync("lsof", ["-nP", `-iTCP:${port}`, "-sTCP:LISTEN", "-t"], {
    encoding: "utf8",
  });
  if (result.status !== 0 || !result.stdout) return null;

  const pid = result.stdout.trim().split("\n")[0];
  return /^\d+$/.test(pid) ? pid : null;
}

/** Full command line of `pid`, or "" if it can't be determined (process gone, no permission, etc). */
function getCommandLine(pid) {
  if (IS_WINDOWS) {
    // PowerShell's CIM query, not wmic - wmic is deprecated/absent on
    // recent Windows, and this is the same lookup already verified
    // reliable for this exact purpose (distinguishing this project's
    // own Next.js process from anything else on the port).
    const result = spawnSync(
      "powershell",
      [
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        `(Get-CimInstance Win32_Process -Filter "ProcessId=${pid}" -ErrorAction SilentlyContinue).CommandLine`,
      ],
      { encoding: "utf8" },
    );
    return result.status === 0 && result.stdout ? result.stdout.trim() : "";
  }

  const result = spawnSync("ps", ["-o", "command=", "-p", pid], { encoding: "utf8" });
  return result.status === 0 && result.stdout ? result.stdout.trim() : "";
}

/** Whether `commandLine` is a `next` process running out of *this* frontend/ directory. */
function isThisProjectsDevServer(commandLine) {
  if (!commandLine) return false;

  const normalized = commandLine.replace(/\\/g, "/").toLowerCase();
  const projectPath = FRONTEND_DIR.replace(/\\/g, "/").toLowerCase();

  return normalized.includes(projectPath) && normalized.includes("next");
}

function runNextDev() {
  const nextBin = path.join(
    FRONTEND_DIR,
    "node_modules",
    ".bin",
    IS_WINDOWS ? "next.cmd" : "next",
  );

  // next.cmd needs shell:true on Windows (a direct, shell-less spawn
  // of a .cmd file throws EINVAL on current Node) - but shell:true
  // *plus* a separate args array makes Node emit the DEP0190
  // deprecation warning (args get concatenated into the shell command
  // without escaping). Passing one pre-assembled command string
  // instead avoids that warning entirely, which is safe here since
  // every piece is a fixed constant (the resolved binary path and a
  // literal port number), never user input that would need escaping.
  const command = IS_WINDOWS
    ? `"${nextBin}" dev -p ${PORT}`
    : nextBin;
  const args = IS_WINDOWS ? [] : ["dev", "-p", String(PORT)];

  const child = spawn(command, args, {
    cwd: FRONTEND_DIR,
    stdio: "inherit",
    shell: IS_WINDOWS,
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code ?? 0);
  });
}

function main() {
  const pid = findListenerPid(PORT);

  if (!pid) {
    runNextDev();
    return;
  }

  const commandLine = getCommandLine(pid);

  if (isThisProjectsDevServer(commandLine)) {
    console.log(`ReelSense frontend is already running at http://localhost:${PORT}`);
    process.exit(0);
  }

  console.error(`Port ${PORT} is occupied by another process (PID ${pid}), not this project's dev server.`);
  console.error(`Please stop that process before starting the ReelSense frontend.`);
  process.exit(1);
}

main();
