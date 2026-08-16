import { access } from "node:fs/promises";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";
import { TokenManager } from "./auth.js";
import { bootstrapPortal } from "./bootstrap.js";
import { PortalClient } from "./client.js";
import type { AppConfig } from "./config.js";
import { getEnvConfig, getMissingEnvVars, validateEnv } from "./config.js";
import { markdownToPdf, titleFromMarkdownPath } from "./convert.js";
import { withRetry } from "./retry.js";

function textResult(data: unknown) {
  return {
    content: [
      {
        type: "text" as const,
        text: typeof data === "string" ? data : JSON.stringify(data, null, 2),
      },
    ],
  };
}

function errorResult(message: string) {
  return {
    isError: true as const,
    content: [{ type: "text" as const, text: message }],
  };
}

export function createServer(
  client: PortalClient,
  config: AppConfig
): McpServer {
  const server = new McpServer({
    name: "ilias-portal",
    version: "1.1.0",
  });

  server.tool(
    "ilias_check_setup",
    "Verify local API configuration and interactive ILIAS session readiness.",
    {},
    { readOnlyHint: true },
    async () => {
      try {
        const missing = getMissingEnvVars();
        const envConfigured = missing.length === 0;

        let profile: { email: string; first_name: string; last_name: string } | null =
          null;
        let sessionStatus: { valid: boolean; message: string } | null = null;

        if (envConfigured) {
          try {
            profile = await client.getProfile();
            sessionStatus = await client.getSessionStatus();
          } catch (err) {
            sessionStatus = {
              valid: false,
              message:
                err instanceof Error
                  ? err.message
                  : "Could not verify ILIAS session. Run ilias_refresh_courses.",
            };
          }
        }

        const readyForPublish =
          envConfigured &&
          (sessionStatus?.valid ?? false) &&
          config.courseIds.length > 0;

        return textResult({
          env_configured: envConfigured,
          missing_env_vars: missing,
          portal_user: profile?.email ?? config.portalEmail,
          ilias_auth_mode:
            config.iliasUsername && config.iliasPassword
              ? "stored_credentials"
              : "interactive_browser",
          course_id: config.courseId || null,
          course_ids: config.courseIds,
          ilias_session: sessionStatus,
          ready_for_publish: readyForPublish,
          hint:
            missing.length > 0
              ? "Fill missing vars in .env.local and restart MCP."
              : !(sessionStatus?.valid ?? false)
                ? "Run ilias_refresh_courses to open the university login and MFA page."
                : config.courseIds.length === 0
                  ? "Interactive session is ready. Provide course_id explicitly for publishing."
                  : "Ready to publish.",
        });
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_list_courses",
    "List cached ILIAS courses from the portal database. Demo flow should prefer ILIAS_COURSE_ID from env instead.",
    {},
    { readOnlyHint: true },
    async () => {
      try {
        const result = await client.listCourses();
        return textResult(result);
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_refresh_courses",
    "Establish or refresh ILIAS session and sync dashboard courses. May open a browser window for MFA. Call when ilias_check_setup reports invalid session.",
    {},
    { readOnlyHint: false },
    async () => {
      try {
        const { result, attempts } = await withRetry(() => client.refreshCourses());
        return textResult({
          success: true,
          message: "Successfully refreshed ILIAS courses and session.",
          retries_attempted: attempts,
          ...result,
          note: "If MFA was required, complete it in the browser window.",
        });
      } catch (err) {
        return textResult({
          success: false,
          message: "Unable to refresh ILIAS courses.",
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  );

  server.tool(
    "ilias_get_course_contents",
    "Fetch live course structure: sections, files, exercises, and other items for a given course ID.",
    { course_id: z.number().int().positive().describe("ILIAS course ID") },
    { readOnlyHint: true },
    async ({ course_id }) => {
      try {
        const result = await client.getCourseContents(course_id);
        return textResult(result);
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_download_file",
    "Download a file from ILIAS by its URL (from course contents). Returns base64-encoded content and filename.",
    {
      url: z.string().url().describe("ILIAS file URL from course contents"),
    },
    { readOnlyHint: true },
    async ({ url }) => {
      try {
        const result = await client.downloadFile(url);
        return textResult({
          filename: result.filename,
          size_bytes: result.size,
          content_base64: result.contentBase64,
        });
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_publish_markdown_as_slides",
    "Demo tool: convert a local markdown file to PDF and publish it as lecture slides to ILIAS. Uses ILIAS_COURSE_ID from env by default. Retries on transient ILIAS errors.",
    {
      markdown_path: z
        .string()
        .min(1)
        .describe("Path to local .md file (e.g. agent/samples/what-is-machine-learning.md)"),
      title: z
        .string()
        .optional()
        .describe("Folder title on ILIAS; defaults to filename"),
      course_id: z
        .number()
        .int()
        .positive()
        .optional()
        .describe("ILIAS course ID; defaults to ILIAS_COURSE_ID from env"),
    },
    { destructiveHint: true },
    async ({ markdown_path, title, course_id }) => {
      const targetCourseId = course_id ?? config.courseId;
      const folderTitle = title ?? titleFromMarkdownPath(markdown_path);

      if (!targetCourseId) {
        return textResult({
          success: false,
          message: "Unable to publish: provide a course_id after interactive login.",
          error: "No default course configured",
          retries_attempted: 0,
        });
      }

      try {
        await access(markdown_path);
      } catch {
        return textResult({
          success: false,
          message: `Unable to publish: markdown file not found at ${markdown_path}`,
          error: "File not found",
          retries_attempted: 0,
        });
      }

      try {
        const pdfPath = await markdownToPdf(markdown_path);

        const { result, attempts } = await withRetry(async () => {
          return client.publishSlides(targetCourseId, {
            title: folderTitle,
            description: `Published from ${markdown_path}`,
            filePaths: [pdfPath],
          });
        });

        return textResult({
          success: true,
          message: `Successfully published "${folderTitle}" to ILIAS course ${targetCourseId}.`,
          url: result.url,
          course_id: targetCourseId,
          markdown_path,
          pdf_path: pdfPath,
          retries_attempted: attempts,
        });
      } catch (err) {
        return textResult({
          success: false,
          message: `Unable to publish "${folderTitle}" to ILIAS course ${targetCourseId}.`,
          error: err instanceof Error ? err.message : String(err),
          course_id: targetCourseId,
          markdown_path,
          retries_attempted: 3,
        });
      }
    }
  );

  server.tool(
    "ilias_publish_assignment",
    "Create an exercise (Übung) in an ILIAS course. Requires moderator/tutor role. Confirm with the user before calling.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      title: z.string().min(1).describe("Assignment title"),
      instruction: z.string().min(1).describe("Assignment instructions for students"),
      deadline: z
        .string()
        .optional()
        .describe("Optional deadline in DD.MM.YYYY HH:MM format (ILIAS locale)"),
      file_path: z
        .string()
        .optional()
        .describe("Optional local file path to attach to the assignment"),
    },
    { destructiveHint: true },
    async ({ course_id, title, instruction, deadline, file_path }) => {
      try {
        const { result, attempts } = await withRetry(() =>
          client.publishAssignment(course_id, {
            title,
            instruction,
            deadline,
            filePath: file_path,
          })
        );
        return textResult({
          success: true,
          message: `Successfully published assignment "${title}".`,
          retries_attempted: attempts,
          ...result,
        });
      } catch (err) {
        return textResult({
          success: false,
          message: `Unable to publish assignment "${title}".`,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  );

  server.tool(
    "ilias_publish_slides",
    "Create a folder and upload lecture slides/files to an ILIAS course. Requires moderator/tutor role. Confirm with the user before calling.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      title: z.string().min(1).describe("Folder title for the slides"),
      description: z.string().optional().describe("Optional folder description"),
      file_paths: z
        .array(z.string())
        .min(1)
        .describe("Local file paths to upload (PDF, PPTX, etc.)"),
    },
    { destructiveHint: true },
    async ({ course_id, title, description, file_paths }) => {
      try {
        const { result, attempts } = await withRetry(() =>
          client.publishSlides(course_id, {
            title,
            description,
            filePaths: file_paths,
          })
        );
        return textResult({
          success: true,
          message: `Successfully published slides folder "${title}".`,
          retries_attempted: attempts,
          ...result,
        });
      } catch (err) {
        return textResult({
          success: false,
          message: `Unable to publish slides folder "${title}".`,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  );

  server.tool(
    "ilias_publish_announcement",
    "Post a news/announcement item to an ILIAS course timeline. Requires moderator/tutor role. Confirm with the user before calling.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      title: z.string().min(1).describe("Announcement title"),
      content: z.string().min(1).describe("Announcement body text"),
      visibility: z
        .enum(["users", "public"])
        .optional()
        .describe('Visibility: "users" (course members) or "public"'),
    },
    { destructiveHint: true },
    async ({ course_id, title, content, visibility }) => {
      try {
        const { result, attempts } = await withRetry(() =>
          client.publishAnnouncement(course_id, {
            title,
            content,
            visibility,
          })
        );
        return textResult({
          success: true,
          message: `Successfully published announcement "${title}".`,
          retries_attempted: attempts,
          ...result,
        });
      } catch (err) {
        return textResult({
          success: false,
          message: `Unable to publish announcement "${title}".`,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }
  );

  return server;
}

export async function main(): Promise<void> {
  const config = validateEnv();
  const tokenManager = new TokenManager(
    config.baseUrl,
    config.portalEmail,
    config.portalPassword
  );

  let client: PortalClient;
  if (process.env.SKIP_BOOTSTRAP === "1") {
    client = new PortalClient(config.baseUrl, tokenManager);
  } else {
    client = await bootstrapPortal(config, tokenManager);
  }

  const server = createServer(client, config);
  const transport = new StdioServerTransport();

  await server.connect(transport);
}

// Re-export for tests
export { getEnvConfig, getMissingEnvVars };
