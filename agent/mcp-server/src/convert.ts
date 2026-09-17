import { mkdtemp, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import { basename, join } from "node:path";
import { tmpdir } from "node:os";

type MdToPdf = (input: { path: string }) => Promise<{ content?: Uint8Array }>;

export async function markdownToPdf(markdownPath: string): Promise<string> {
  const baseName = basename(markdownPath, ".md");
  const dir = await mkdtemp(join(tmpdir(), "ilias-pdf-"));
  const pdfPath = join(dir, `${baseName}.pdf`);

  let mdToPdf: MdToPdf;
  try {
    // The renderer is an opt-in authoring add-on, so core installs ship no Puppeteer.
    ({ mdToPdf } = createRequire(import.meta.url)("md-to-pdf") as {
      mdToPdf: MdToPdf;
    });
  } catch {
    throw new Error(
      "Markdown-to-PDF is optional and is not installed. Install the authoring add-on " +
        "with PUPPETEER_SKIP_DOWNLOAD=true and an installed Chrome executable."
    );
  }
  const pdf = await mdToPdf({ path: markdownPath });
  if (!pdf?.content) {
    throw new Error(`Failed to convert markdown to PDF: ${markdownPath}`);
  }

  await writeFile(pdfPath, pdf.content);
  return pdfPath;
}

export function titleFromMarkdownPath(markdownPath: string): string {
  const base = basename(markdownPath, ".md");
  return base
    .split(/[-_]/)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}
