import { afterEach, describe, it, expect } from "vitest";
import { getEnvConfig, getMissingEnvVars, validateEnv } from "../../src/config";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

describe("config", () => {
  it("reports missing env vars", () => {
    process.env = {};
    expect(getMissingEnvVars()).toContain("PORTAL_EMAIL");
    expect(getMissingEnvVars()).toContain("ILIAS_COURSE_ID");
    expect(getEnvConfig()).toBeNull();
  });

  it("parses valid env config", () => {
    process.env = {
      PORTAL_EMAIL: "test@example.com",
      PORTAL_PASSWORD: "secret",
      ILIAS_USERNAME: "zxofp67",
      ILIAS_PASSWORD: "ilias-secret",
      ILIAS_COURSE_ID: "5658784",
      ILIAS_COURSE_IDS: "5658784,5658785",
      API_BASE_URL: "http://localhost:8000/",
    };

    const config = validateEnv();
    expect(config.portalEmail).toBe("test@example.com");
    expect(config.iliasUsername).toBe("zxofp67");
    expect(config.courseId).toBe(5658784);
    expect(config.courseIds).toEqual([5658784, 5658785]);
    expect(config.baseUrl).toBe("http://localhost:8000");
  });

  it("rejects non-zx ILIAS username", () => {
    process.env = {
      PORTAL_EMAIL: "test@example.com",
      PORTAL_PASSWORD: "secret",
      ILIAS_USERNAME: "abofp67",
      ILIAS_PASSWORD: "ilias-secret",
      ILIAS_COURSE_ID: "5658784",
    };

    expect(() => validateEnv()).toThrow(/must start with 'zx'/);
  });
});
