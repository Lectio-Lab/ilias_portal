type FetchFn = typeof fetch;

export class TokenManager {
  constructor(
    private readonly token: string,
    private readonly fetchFn: FetchFn = fetch
  ) {}

  async authenticatedFetch(
    url: string,
    init: RequestInit = {}
  ): Promise<Response> {
    const headers = new Headers(init.headers);
    // A generated installation-local secret replaces the old database/JWT flow.
    headers.set("Authorization", `Bearer ${this.token}`);
    return this.fetchFn(url, { ...init, headers });
  }
}
