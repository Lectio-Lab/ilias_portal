import { describe, expect, it, vi } from "vitest";
import { TokenManager } from "../../src/auth";

describe("TokenManager", () => {
  it("sends the installation-local bearer secret on every request", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200 });
    const manager = new TokenManager("local-token", fetchMock);

    await manager.authenticatedFetch("http://127.0.0.1:8010/api/ilias/courses/");

    const [, init] = fetchMock.mock.calls[0];
    expect(new Headers(init.headers).get("Authorization")).toBe("Bearer local-token");
  });
});
