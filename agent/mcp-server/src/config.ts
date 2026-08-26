export interface AppConfig {
  baseUrl: string;
  portalEmail: string;
  portalPassword: string;
  iliasUsername: string;
  iliasPassword: string;
  courseId: number;
  courseIds: number[];
}

const REQUIRED_ENV_KEYS = [
  "PORTAL_EMAIL",
  "PORTAL_PASSWORD",
] as const;

function credentialsHint(): string {
  const home = process.env.ILIAS_PORTAL_HOME;
  const path =
    process.env.DOTENV_PATH ??
    (home
      ? `${home}/agent/credentials/.env.local`
      : "agent/credentials/.env.local");
  return `Copy agent/credentials/.env.local.example to ${path} and fill in all fields.`;
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
    baseUrl: (process.env.API_BASE_URL ?? "http://localhost:8000").replace(
      /\/$/,
      ""
    ),
    portalEmail: process.env.PORTAL_EMAIL!.trim(),
    portalPassword: process.env.PORTAL_PASSWORD!.trim(),
    iliasUsername: process.env.ILIAS_USERNAME?.trim() ?? "",
    iliasPassword: process.env.ILIAS_PASSWORD?.trim() ?? "",
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

  if (config.iliasPassword) {
    throw new Error(
      "ILIAS_PASSWORD must stay blank. University passwords are never stored. " +
        "Clear ILIAS_PASSWORD in your .env.local and complete login via " +
        "ilias_refresh_courses in the browser MFA window."
    );
  }

  if (config.iliasUsername && !config.iliasUsername.startsWith("zx")) {
    throw new Error(
      "ILIAS_USERNAME must start with 'zx' and be your own account, or stay blank. " +
        "Update ILIAS_USERNAME in your .env.local credentials file."
    );
  }

  return config;
}
