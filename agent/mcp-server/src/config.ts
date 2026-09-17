export interface AppConfig {
  baseUrl: string;
  portalLocalToken: string;
  courseId: number;
  courseIds: number[];
}

const REQUIRED_ENV_KEYS = ["PORTAL_LOCAL_TOKEN"] as const;

function credentialsHint(): string {
  const home = process.env.ILIAS_PORTAL_HOME;
  const path =
    process.env.DOTENV_PATH ??
    (home
      ? `${home}/agent/credentials/.env.local`
      : "agent/credentials/.env.local");
  return `Run ./install.sh to create ${path} with this installation's local bearer token.`;
}

export function getMissingEnvVars(): string[] {
  const missing: string[] = [];
  for (const key of REQUIRED_ENV_KEYS) {
    if (!process.env[key]?.trim()) {
      missing.push(key);
    }
  }
  return missing;
}

function parseCourseIds(): number[] {
  const primary = process.env.ILIAS_COURSE_ID?.trim();
  const extra = process.env.ILIAS_COURSE_IDS?.trim();

  const ids = new Set<number>();
  if (primary) {
    const n = parseInt(primary, 10);
    if (!Number.isNaN(n) && n > 0) ids.add(n);
  }
  if (extra) {
    for (const part of extra.split(",")) {
      const n = parseInt(part.trim(), 10);
      if (!Number.isNaN(n) && n > 0) ids.add(n);
    }
  }
  return Array.from(ids);
}

export function getEnvConfig(): AppConfig | null {
  const missing = getMissingEnvVars();
  if (missing.length > 0) return null;

  const courseIds = parseCourseIds();

  return {
    baseUrl: (process.env.API_BASE_URL ?? "http://127.0.0.1:8010").replace(
      /\/$/,
      ""
    ),
    portalLocalToken: process.env.PORTAL_LOCAL_TOKEN!.trim(),
    courseId: courseIds[0] ?? 0,
    courseIds,
  };
}

export function validateEnv(): AppConfig {
  const missing = getMissingEnvVars();
  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables: ${missing.join(", ")}. ` +
        credentialsHint()
    );
  }

  const config = getEnvConfig();
  if (!config) throw new Error("Portal configuration is incomplete.");

  const endpoint = new URL(config.baseUrl);
  if (!["127.0.0.1", "localhost", "::1"].includes(endpoint.hostname)) {
    throw new Error("API_BASE_URL must target the local ILIAS service.");
  }

  return config;
}
