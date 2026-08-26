import { describe, it, expect } from "vitest";
import { mapApiError } from "../../src/errors";

describe("mapApiError", () => {
  it("maps 401 to credential refresh message", () => {
    const result = mapApiError(401, { detail: "Token expired" });
    expect(result.message).toContain("authentication");
    expect(result.recoverable).toBe(true);
  });

  it("maps 404 ILIAS credentials to setup message", () => {
    const result = mapApiError(404, { detail: "No ILIAS credentials saved yet." });
    expect(result.message).toContain("ILIAS credentials");
    expect(result.recoverable).toBe(true);
  });

  it("maps 502 to ILIAS connectivity message", () => {
    const result = mapApiError(502, { detail: "Failed to fetch courses" });
    expect(result.message).toContain("ILIAS");
    expect(result.recoverable).toBe(true);
  });

  it("maps unknown errors with detail field", () => {
    const result = mapApiError(400, { detail: "title is required." });
    expect(result.message).toBe("title is required.");
    expect(result.recoverable).toBe(false);
  });
});
