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
    version: "1.3.0",
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

        let sessionStatus: { valid: boolean; message: string } | null = null;

        if (envConfigured) {
          try {
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
          portal_user: "installation-local bearer token",
          ilias_auth_mode: "interactive_browser",
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
    "ilias_find_course_items",
    "Search live course items by the user's words and return ranked candidates with their exact ILIAS URLs. Exercise matches include current title, description, assignment instructions, deadline, and assignment IDs when editable. Use this before editing; never guess an item URL or silently choose among ambiguous matches.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      query: z
        .string()
        .min(1)
        .max(500)
        .describe("Words identifying the item, such as its title"),
      item_type: z
        .string()
        .optional()
        .describe('Optional ILIAS type filter, for example "Exercise"'),
      limit: z
        .number()
        .int()
        .min(1)
        .max(20)
        .optional()
        .describe("Maximum candidates to return; defaults to 10"),
    },
    { readOnlyHint: true },
    async ({ course_id, query, item_type, limit }) => {
      try {
        const result = await client.findCourseItems(
          course_id,
          query,
          item_type,
          limit
        );
        return textResult(result);
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_edit_exercise",
    "Edit the exact exercise URL returned by ilias_find_course_items, then re-fetch it and verify the update. Supports the exercise title/description and assignment title/instructions/deadline. Confirm the exact changes with the user before calling. Do not call when search is ambiguous, and do not automatically retry this write.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      exercise_url: z
        .string()
        .url()
        .describe("Exact exercise URL returned by ilias_find_course_items"),
      expected_title: z
        .string()
        .min(1)
        .describe("Current exact exercise title returned by the find tool"),
      expected_description: z
        .string()
        .nullable()
        .optional()
        .describe("Current description; required when changing description"),
      expected_assignment_title: z
        .string()
        .optional()
        .describe("Current assignment title; required when changing it"),
      expected_instruction: z
        .string()
        .optional()
        .describe("Current instructions; required when changing them"),
      expected_deadline: z
        .string()
        .nullable()
        .optional()
        .describe("Current deadline, or null when absent; required when changing it"),
      title: z
        .string()
        .min(1)
        .optional()
        .describe("New exercise container title"),
      description: z
        .string()
        .optional()
        .describe("New exercise container description; may be blank"),
      assignment_id: z
        .number()
        .int()
        .positive()
        .optional()
        .describe("Required for assignment edits when the exercise has multiple units"),
      assignment_title: z
        .string()
        .min(1)
        .optional()
        .describe("New assignment-unit title"),
      instruction: z
        .string()
        .optional()
        .describe("New student-facing assignment instructions; may be blank"),
      deadline: z
        .string()
        .optional()
        .describe("New DD.MM.YYYY HH:MM deadline; pass an empty string to remove it"),
    },
    { destructiveHint: true, idempotentHint: false },
    async ({
      course_id,
      exercise_url,
      expected_title,
      expected_description,
      expected_assignment_title,
      expected_instruction,
      expected_deadline,
      title,
      description,
      assignment_id,
      assignment_title,
      instruction,
      deadline,
    }) => {
      if (
        title === undefined &&
        description === undefined &&
        assignment_title === undefined &&
        instruction === undefined &&
        deadline === undefined
      ) {
        return errorResult(
          "Provide at least one field to edit: title, description, assignment_title, instruction, or deadline."
        );
      }
      const missingExpected = [
        description !== undefined && expected_description === undefined
          ? "expected_description"
          : null,
        assignment_title !== undefined && expected_assignment_title === undefined
          ? "expected_assignment_title"
          : null,
        instruction !== undefined && expected_instruction === undefined
          ? "expected_instruction"
          : null,
        deadline !== undefined && expected_deadline === undefined
          ? "expected_deadline"
          : null,
      ].filter(Boolean);
      if (missingExpected.length > 0) {
        return errorResult(
          `Provide current values from ilias_find_course_items before editing: ${missingExpected.join(", ")}.`
        );
      }
      try {
        const result = await client.editExercise(course_id, {
          exerciseUrl: exercise_url,
          expectedTitle: expected_title,
          expectedDescription: expected_description,
          expectedAssignmentTitle: expected_assignment_title,
          expectedInstruction: expected_instruction,
          expectedDeadline: expected_deadline,
          title,
          description,
          assignmentId: assignment_id,
          assignmentTitle: assignment_title,
          instruction,
          deadline,
        });
        return textResult({
          ...result,
          message: `Successfully updated and verified "${result.exercise.title}".`,
        });
      } catch (err) {
        return textResult({
          success: false,
          verified: false,
          message: "Unable to update the exercise.",
          error: err instanceof Error ? err.message : String(err),
          url: exercise_url,
        });
      }
    }
  );

  server.tool(
    "ilias_find_grade_target",
    "Resolve one exact exercise participant and return the current assignment status, mark, and tutor comment. Use the exact participant login supplied by the instructor. This tool never lists the full roster and never changes a grade.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      exercise_url: z
        .string()
        .url()
        .describe("Exact exercise URL returned by ilias_find_course_items"),
      assignment_id: z
        .number()
        .int()
        .positive()
        .describe("Exact assignment ID returned by ilias_find_course_items"),
      participant_login: z
        .string()
        .min(1)
        .max(255)
        .describe("Exact ILIAS login supplied by the instructor"),
    },
    { readOnlyHint: true },
    async ({ course_id, exercise_url, assignment_id, participant_login }) => {
      try {
        const result = await client.findGradeTarget(course_id, {
          exerciseUrl: exercise_url,
          assignmentId: assignment_id,
          participantLogin: participant_login,
        });
        return textResult(result);
      } catch (err) {
        return errorResult(err instanceof Error ? err.message : String(err));
      }
    }
  );

  server.tool(
    "ilias_post_grade",
    "Post instructor-supplied grading fields for one exact exercise participant, then re-fetch and verify them. Never calculate, recommend, infer, or choose a grade. First call ilias_find_grade_target, show the exact target and before/after values, and obtain explicit instructor confirmation. Do not retry this write automatically.",
    {
      course_id: z.number().int().positive().describe("ILIAS course ID"),
      exercise_url: z
        .string()
        .url()
        .describe("Exact exercise URL used for grade-target discovery"),
      assignment_id: z
        .number()
        .int()
        .positive()
        .describe("Exact assignment ID used for grade-target discovery"),
      participant_login: z
        .string()
        .min(1)
        .max(255)
        .describe("Exact ILIAS login supplied by the instructor"),
      expected_exercise_title: z
        .string()
        .min(1)
        .describe("Current exact exercise title from ilias_find_grade_target"),
      expected_assignment_title: z
        .string()
        .min(1)
        .describe("Current exact assignment title from ilias_find_grade_target"),
      expected_status: z
        .enum(["notgraded", "passed", "failed"])
        .describe("Current status from ilias_find_grade_target"),
      expected_mark: z
        .string()
        .max(32)
        .describe("Current mark from ilias_find_grade_target; may be blank"),
      expected_comment: z
        .string()
        .nullable()
        .describe("Current tutor comment from ilias_find_grade_target, or null"),
      status: z
        .enum(["notgraded", "passed", "failed"])
        .optional()
        .describe("New instructor-supplied status"),
      mark: z
        .string()
        .max(32)
        .optional()
        .describe("New instructor-supplied mark; may be blank"),
      comment: z
        .string()
        .optional()
        .describe("New instructor-supplied tutor comment; may be blank"),
    },
    { destructiveHint: true, idempotentHint: false },
    async ({
      course_id,
      exercise_url,
      assignment_id,
      participant_login,
      expected_exercise_title,
      expected_assignment_title,
      expected_status,
      expected_mark,
      expected_comment,
      status,
      mark,
      comment,
    }) => {
      if (status === undefined && mark === undefined && comment === undefined) {
        return errorResult(
          "Provide at least one instructor-supplied field: status, mark, or comment."
        );
      }
      try {
        const result = await client.postGrade(course_id, {
          exerciseUrl: exercise_url,
          assignmentId: assignment_id,
          participantLogin: participant_login,
          expectedExerciseTitle: expected_exercise_title,
          expectedAssignmentTitle: expected_assignment_title,
          expectedStatus: expected_status,
          expectedMark: expected_mark,
          expectedComment: expected_comment,
          status,
          mark,
          comment,
        });
        return textResult({
          ...result,
          message: `Successfully posted and verified the supplied grade for ${result.grade.participant_login}.`,
        });
      } catch (err) {
        return textResult({
          success: false,
          verified: false,
          message: "Unable to post or verify the supplied grade.",
          error: err instanceof Error ? err.message : String(err),
          url: exercise_url,
        });
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
  const tokenManager = new TokenManager(config.portalLocalToken);

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
