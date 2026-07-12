export interface MappedError {
  message: string;
  recoverable: boolean;
  action?: string;
}

export function mapApiError(
  status: number,
  body: Record<string, unknown>
): MappedError {
  const detail =
    typeof body.detail === "string"
      ? body.detail
      : typeof body.message === "string"
        ? body.message
        : JSON.stringify(body);

  if (status === 401) {
    return {
      message: `ILIAS authentication failed: ${detail}`,
      recoverable: true,
      action:
        "Run ilias_refresh_courses with a browser available to complete MFA, or re-save ILIAS credentials via the portal.",
    };
  }

  if (status === 404 && detail.toLowerCase().includes("ilias credentials")) {
    return {
      message: detail,
      recoverable: true,
      action:
        "Set ILIAS_USERNAME and ILIAS_PASSWORD in your .env.local credentials file, then restart MCP.",
    };
  }

  if (status === 502 || status === 503) {
    return {
      message: `ILIAS service error: ${detail}`,
      recoverable: true,
      action: "Check backend logs and ILIAS availability. Retry after a few seconds.",
    };
  }

  if (status === 400) {
    return {
      message: detail,
      recoverable: false,
      action: "Fix the request parameters and retry.",
    };
  }

  if (status === 422) {
    return {
      message: `ILIAS rejected the operation: ${detail}`,
      recoverable: false,
      action: "Verify course permissions and field values.",
    };
  }

  return {
    message: `API error (${status}): ${detail}`,
    recoverable: status >= 500,
    action: status >= 500 ? "Retry after a few seconds." : undefined,
  };
}

export function formatToolError(error: MappedError): string {
  const parts = [error.message];
  if (error.action) {
    parts.push(`Suggested action: ${error.action}`);
  }
  return parts.join("\n");
}
