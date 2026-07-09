import { describe, it, expect, vi } from "vitest";
import { withRetry } from "../../src/retry";

describe("withRetry", () => {
  it("returns on first success", async () => {
    const fn = vi.fn().mockResolvedValue("ok");
    const { result, attempts } = await withRetry(fn);
    expect(result).toBe("ok");
    expect(attempts).toBe(1);
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("retries on retryable errors", async () => {
    const fn = vi
      .fn()
      .mockRejectedValueOnce(new Error("ILIAS service error (502)"))
      .mockResolvedValue("ok");

    const { result, attempts } = await withRetry(fn, { baseDelayMs: 1 });
    expect(result).toBe("ok");
    expect(attempts).toBe(2);
  });

  it("throws after max attempts", async () => {
    const fn = vi.fn().mockRejectedValue(new Error("ILIAS service error (503)"));

    await expect(
      withRetry(fn, { maxAttempts: 2, baseDelayMs: 1 })
    ).rejects.toThrow("503");
    expect(fn).toHaveBeenCalledTimes(2);
  });
});
