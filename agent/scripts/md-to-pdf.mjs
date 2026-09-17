#!/usr/bin/env node
/**
 * Convert a markdown file to PDF using md-to-pdf.
 * Usage: node agent/scripts/md-to-pdf.mjs input.md [output.pdf]
 */
import { writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { createRequire } from "node:module";

let mdToPdf;
try {
  ({ mdToPdf } = createRequire(import.meta.url)("md-to-pdf"));
} catch {
  console.error("Markdown-to-PDF is optional. Install the authoring add-on with PUPPETEER_SKIP_DOWNLOAD=true and installed Chrome.");
  process.exit(2);
}

const input = process.argv[2];
if (!input) {
  console.error("Usage: node md-to-pdf.mjs <input.md> [output.pdf]");
  process.exit(1);
}

const output =
  process.argv[3] ?? join(process.cwd(), `${basename(input, ".md")}.pdf`);

const pdf = await mdToPdf({ path: input });
if (!pdf?.content) {
  console.error(`Failed to convert ${input}`);
  process.exit(1);
}

await writeFile(output, pdf.content);
console.log(output);
