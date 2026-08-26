#!/usr/bin/env node
import { main } from "./index.js";

main().catch((err) => {
  console.error(
    "ilias-portal MCP server failed to start:",
    err instanceof Error ? err.message : err
  );
  process.exit(1);
});
