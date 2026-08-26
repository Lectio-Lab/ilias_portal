import type { AppConfig } from "./config.js";
import { TokenManager } from "./auth.js";
import { PortalClient } from "./client.js";

export async function bootstrapPortal(
  config: AppConfig,
  tokenManager: TokenManager
): Promise<PortalClient> {
  const client = new PortalClient(config.baseUrl, tokenManager);

  try {
    await tokenManager.login();
  } catch {
    await client.registerPortal(
      config.portalEmail,
      config.portalPassword,
      "Agent",
      "User"
    );
    await tokenManager.login();
  }

  // Never POST university credentials. ILIAS auth is interactive browser MFA;
  // only session cookies are persisted by the backend after refresh.

  return client;
}
