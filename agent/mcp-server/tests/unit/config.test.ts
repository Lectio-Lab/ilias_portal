import { afterEach, describe, expect, it } from "vitest";
import { getEnvConfig, getMissingEnvVars, validateEnv } from "../../src/config";

const ORIGINAL_ENV = { ...process.env };

afterEach(() => {
  process.env = { ...ORIGINAL_ENV };
});

describe("config", () => {
  it("requires the installation-local bearer token", () => {
    process.env = {};
    expect(getMissingEnvVars()).toEqual(["PORTAL_LOCAL_TOKEN"]);
    expect(getEnvConfig()).toBeNull();
  });

  it("accepts the loopback local service configuration", () => {
    process.env = {
      PORTAL_LOCAL_TOKEN: "generated-local-secret",
      API_BASE_URL: "http://127.0.0.1:8010/",
      ILIAS_COURSE_ID: "5658784",
      ILIAS_COURSE_IDS: "5658784,5658785",
    };
    const config = validateEnv();
    expect(config.baseUrl).toBe("http://127.0.0.1:8010");
    expect(config.courseIds).toEqual([5658784, 5658785]);
  });

  it("rejects a non-local API endpoint", () => {
    process.env = {
      PORTAL_LOCAL_TOKEN: "generated-local-secret",
      API_BASE_URL: "https://example.com",
    };
    expect(() => validateEnv()).toThrow(/local ILIAS service/);
  });
});
