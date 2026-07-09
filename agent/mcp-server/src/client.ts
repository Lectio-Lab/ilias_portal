import { readFile } from "node:fs/promises";
import { basename } from "node:path";
import { TokenManager } from "./auth.js";
import { formatToolError, mapApiError } from "./errors.js";

export class PortalClient {
  constructor(
    private readonly baseUrl: string,
    private readonly tokenManager: TokenManager
  ) {}

  private async requestJson<T>(
    path: string,
    init: RequestInit = {}
  ): Promise<T> {
    const response = await this.tokenManager.authenticatedFetch(
      `${this.baseUrl}${path}`,
      init
    );

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const mapped = mapApiError(response.status, body);
      throw new Error(formatToolError(mapped));
    }

    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  }

  async getProfile() {
    return this.requestJson<{
      id: number;
      email: string;
      first_name: string;
      last_name: string;
    }>("/api/auth/profile/");
  }

  async getIliasCredentials() {
    const response = await this.tokenManager.authenticatedFetch(
      `${this.baseUrl}/api/auth/ilias-credentials/`
    );

    if (response.status === 404) {
      return null;
    }

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const mapped = mapApiError(response.status, body);
      throw new Error(formatToolError(mapped));
    }

    return (await response.json()) as {
      ilias_username: string;
      created_at: string;
      updated_at: string;
    };
  }

  async getSessionStatus() {
    return this.requestJson<{ valid: boolean; message: string }>(
      "/api/ilias/session/status/"
    );
  }

  async registerPortal(
    email: string,
    password: string,
    firstName: string,
    lastName: string
  ) {
    const response = await fetch(`${this.baseUrl}/api/auth/register/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email,
        password,
        first_name: firstName,
        last_name: lastName,
      }),
    });

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const detail =
        typeof body.email === "object"
          ? JSON.stringify(body)
          : typeof body.detail === "string"
            ? body.detail
            : JSON.stringify(body);
      throw new Error(`Portal registration failed (${response.status}): ${detail}`);
    }

    return response.json();
  }

  async saveIliasCredentials(username: string, password: string) {
    return this.requestJson<{ ilias_username: string }>(
      "/api/auth/ilias-credentials/",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ilias_username: username,
          ilias_password: password,
        }),
      }
    );
  }

  async listCourses() {
    return this.requestJson<{
      count: number;
      courses: Array<{
        course_id: number;
        title: string;
        url: string;
        role: string;
        last_refreshed: string;
      }>;
    }>("/api/ilias/courses/");
  }

  async refreshCourses() {
    return this.requestJson<{
      count: number;
      courses: Array<{
        course_id: number;
        title: string;
        url: string;
        role: string;
        last_refreshed: string;
      }>;
    }>("/api/ilias/courses/refresh/", { method: "POST" });
  }

  async getCourseContents(courseId: number) {
    return this.requestJson<{
      course_title: string | null;
      sections: Array<{
        section: string;
        items: Array<{
          title: string;
          url: string;
          type: string | null;
          properties: Record<string, string>;
        }>;
      }>;
    }>(`/api/ilias/courses/${courseId}/contents/`);
  }

  async downloadFile(url: string) {
    const encoded = encodeURIComponent(url);
    const response = await this.tokenManager.authenticatedFetch(
      `${this.baseUrl}/api/ilias/download/?url=${encoded}`
    );

    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as Record<
        string,
        unknown
      >;
      const mapped = mapApiError(response.status, body);
      throw new Error(formatToolError(mapped));
    }

    const buffer = Buffer.from(await response.arrayBuffer());
    const disposition = response.headers.get("Content-Disposition") ?? "";
    const filenameMatch = disposition.match(/filename="([^"]+)"/);
    const filename = filenameMatch?.[1] ?? "download";

    return { filename, size: buffer.length, contentBase64: buffer.toString("base64") };
  }

  async publishAssignment(
    courseId: number,
    data: {
      title: string;
      instruction: string;
      deadline?: string;
      filePath?: string;
    }
  ) {
    if (data.filePath) {
      const fileContent = await readFile(data.filePath);
      const form = new FormData();
      form.append("title", data.title);
      form.append("instruction", data.instruction);
      if (data.deadline) form.append("deadline", data.deadline);
      form.append(
        "file",
        new Blob([fileContent]),
        basename(data.filePath)
      );

      return this.requestJson<{ url: string }>(
        `/api/ilias/courses/${courseId}/publish/assignment/`,
        { method: "POST", body: form }
      );
    }

    return this.requestJson<{ url: string }>(
      `/api/ilias/courses/${courseId}/publish/assignment/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: data.title,
          instruction: data.instruction,
          deadline: data.deadline ?? "",
        }),
      }
    );
  }

  async publishSlides(
    courseId: number,
    data: {
      title: string;
      description?: string;
      filePaths: string[];
    }
  ) {
    const form = new FormData();
    form.append("title", data.title);
    if (data.description) form.append("description", data.description);

    for (const filePath of data.filePaths) {
      const fileContent = await readFile(filePath);
      const name = basename(filePath);
      form.append("file", new Blob([fileContent]), name);
    }

    return this.requestJson<{ url: string }>(
      `/api/ilias/courses/${courseId}/publish/slides/`,
      { method: "POST", body: form }
    );
  }

  async publishAnnouncement(
    courseId: number,
    data: {
      title: string;
      content: string;
      visibility?: "users" | "public";
    }
  ) {
    return this.requestJson<{ url: string }>(
      `/api/ilias/courses/${courseId}/publish/announcement/`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: data.title,
          content: data.content,
          visibility: data.visibility ?? "users",
        }),
      }
    );
  }
}
