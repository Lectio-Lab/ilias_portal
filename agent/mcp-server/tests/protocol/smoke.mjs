#!/usr/bin/env node
/**
 * Protocol smoke test for the ILIAS Portal MCP server.
 * Verifies the server starts and responds to tools/list via stdio JSON-RPC.
 *
 * Usage: npm run smoke
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { readFileSync, existsSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../../..");
const credsFile = resolve(repoRoot, "agent/credentials/.env.local");
const cliPath = resolve(__dirname, "../../dist/cli.js");

function loadEnv(path) {
  const env = { ...process.env };
  if (existsSync(path)) {
    for (const line of readFileSync(path, "utf8").split("\n")) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq === -1) continue;
      env[trimmed.slice(0, eq).trim()] = trimmed.slice(eq + 1).trim();
    }
  }

  // Smoke-test defaults (protocol check only; no live API calls)
  env.PORTAL_EMAIL = env.PORTAL_EMAIL || "smoke-test@example.com";
  env.PORTAL_PASSWORD = env.PORTAL_PASSWORD || "smoke-test-password";
  env.ILIAS_USERNAME = env.ILIAS_USERNAME || "zxtest1";
  env.ILIAS_PASSWORD = env.ILIAS_PASSWORD || "smoke-test-password";
  env.ILIAS_COURSE_ID = env.ILIAS_COURSE_ID || "5658784";
  env.API_BASE_URL = env.API_BASE_URL || "http://localhost:8000";

  return env;
}

function send(proc, message) {
  proc.stdin.write(JSON.stringify(message) + "\n");
}

function readMessages(proc, timeoutMs = 8000) {
  return new Promise((resolveMessages, reject) => {
    let buffer = "";
    const messages = [];

    proc.stdout.on("data", (chunk) => {
      buffer += chunk.toString();
      let index;
      while ((index = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, index).trim();
        buffer = buffer.slice(index + 1);
        if (!line) continue;
        try {
          messages.push(JSON.parse(line));
        } catch {
          // ignore non-json lines
        }
      }
    });

    proc.on("error", reject);

    setTimeout(() => {
      proc.kill();
      resolveMessages(messages);
    }, timeoutMs);
  });
}

async function main() {
  const env = loadEnv(credsFile);
  const proc = spawn("node", [cliPath], {
    env: { ...env, SKIP_BOOTSTRAP: "1" },
    stdio: ["pipe", "pipe", "pipe"],
  });

  proc.stderr.on("data", (d) => process.stderr.write(d));

  send(proc, {
    jsonrpc: "2.0",
    id: 1,
    method: "initialize",
    params: {
      protocolVersion: "2024-11-05",
      capabilities: {},
      clientInfo: { name: "smoke-test", version: "1.0.0" },
    },
  });

  send(proc, { jsonrpc: "2.0", method: "notifications/initialized" });

  send(proc, {
    jsonrpc: "2.0",
    id: 2,
    method: "tools/list",
    params: {},
  });

  const messages = await readMessages(proc);

  const toolsResponse = messages.find((m) => m.id === 2);
  if (!toolsResponse?.result?.tools) {
    console.error("FAIL: tools/list did not return tools");
    console.error("Messages received:", JSON.stringify(messages, null, 2));
    process.exit(1);
  }

  const toolNames = toolsResponse.result.tools.map((t) => t.name);
  const expected = [
    "ilias_check_setup",
    "ilias_list_courses",
    "ilias_refresh_courses",
    "ilias_get_course_contents",
    "ilias_find_course_items",
    "ilias_edit_exercise",
    "ilias_download_file",
    "ilias_publish_markdown_as_slides",
    "ilias_publish_assignment",
    "ilias_publish_slides",
    "ilias_publish_announcement",
  ];

  const missing = expected.filter((n) => !toolNames.includes(n));
  if (missing.length > 0) {
    console.error("FAIL: missing tools:", missing.join(", "));
    process.exit(1);
  }

  console.log("PASS: MCP server exposes", toolNames.length, "tools");
}

main().catch((err) => {
  console.error("Smoke test failed:", err);
  process.exit(1);
});
