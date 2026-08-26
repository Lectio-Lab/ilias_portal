import { describe, it, expect, beforeEach, vi } from "vitest";
import { TokenManager } from "../../src/auth";

describe("TokenManager", () => {
  const baseUrl = "http://localhost:8000";
  const email = "test@example.com";
  const password = "testpassword";

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("logs in and returns access token", async () => {
    const fetchMock = vi.fn().mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        access: "access-token-123",
        refresh: "refresh-token-456",
      }),
    });

    const manager = new TokenManager(baseUrl, email, password, fetchMock);
    const token = await manager.getAccessToken();

    expect(token).toBe("access-token-123");
    expect(fetchMock).toHaveBeenCalledWith(
      `${baseUrl}/api/auth/login/`,
      expect.objectContaining({ method: "POST" })
    );
  });

  it("refreshes token on 401 and retries", async () => {
    let callCount = 0;
    const fetchMock = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes("/login/")) {
        return {
          ok: true,
          json: async () => ({ access: "old-access", refresh: "refresh-token" }),
        };
      }
      if (url.includes("/refresh/")) {
        return {
          ok: true,
          json: async () => ({ access: "new-access", refresh: "new-refresh" }),
        };
      }
      callCount++;
      if (callCount === 1) {
        return { ok: false, status: 401, json: async () => ({ detail: "expired" }) };
      }
      return { ok: true, status: 200, json: async () => ({ count: 0, courses: [] }) };
    });

    const manager = new TokenManager(baseUrl, email, password, fetchMock);
    const response = await manager.authenticatedFetch(`${baseUrl}/api/ilias/courses/`);

    expect(response.ok).toBe(true);
    expect(fetchMock).toHaveBeenCalledWith(
      `${baseUrl}/api/auth/refresh/`,
      expect.objectContaining({ method: "POST" })
    );
  });
});
