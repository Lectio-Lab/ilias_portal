import { mkdtemp, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { tmpdir } from "node:os";
import { mdToPdf } from "md-to-pdf";

export async function markdownToPdf(markdownPath: string): Promise<string> {
  const baseName = basename(markdownPath, ".md");
  const dir = await mkdtemp(join(tmpdir(), "ilias-pdf-"));
  const pdfPath = join(dir, `${baseName}.pdf`);

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
