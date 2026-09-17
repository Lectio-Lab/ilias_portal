import type { AppConfig } from "./config.js";
import { TokenManager } from "./auth.js";
import { PortalClient } from "./client.js";

export async function bootstrapPortal(
  config: AppConfig,
  tokenManager: TokenManager
): Promise<PortalClient> {
  // The service is provisioned locally during install; no account registration exists.
  return new PortalClient(config.baseUrl, tokenManager);
}
