type FetchFn = typeof fetch;

interface TokenPair {
  access: string;
  refresh: string;
}

export class TokenManager {
  private accessToken: string | null = null;
  private refreshToken: string | null = null;
  private loginPromise: Promise<void> | null = null;

  constructor(
    private readonly baseUrl: string,
    private readonly email: string,
    private readonly password: string,
    private readonly fetchFn: FetchFn = fetch
  ) {}

  async getAccessToken(): Promise<string> {
    if (!this.accessToken) {
      await this.login();
    }
    return this.accessToken!;
  }

  async login(): Promise<void> {
    if (this.loginPromise) {
      return this.loginPromise;
    }

    this.loginPromise = this.performLogin();
    try {
      await this.loginPromise;
    } finally {
      this.loginPromise = null;
    }
  }

  private async performLogin(): Promise<void> {
    const response = await this.fetchFn(`${this.baseUrl}/api/auth/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: this.email, password: this.password }),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(
        `Portal login failed (${response.status}): ${
          typeof body.detail === "string" ? body.detail : "Invalid credentials"
        }`
      );
    }

    const tokens = (await response.json()) as TokenPair;
    this.accessToken = tokens.access;
    this.refreshToken = tokens.refresh;
  }

  private async refresh(): Promise<void> {
    if (!this.refreshToken) {
      await this.login();
      return;
    }

    const response = await this.fetchFn(`${this.baseUrl}/api/auth/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: this.refreshToken }),
    });

    if (!response.ok) {
      this.accessToken = null;
      this.refreshToken = null;
      await this.login();
      return;
    }

    const tokens = (await response.json()) as TokenPair;
    this.accessToken = tokens.access;
    if (tokens.refresh) {
      this.refreshToken = tokens.refresh;
    }
  }

  async authenticatedFetch(
    url: string,
    init: RequestInit = {}
  ): Promise<Response> {
    const token = await this.getAccessToken();
    const headers = new Headers(init.headers);
    headers.set("Authorization", `Bearer ${token}`);

    let response = await this.fetchFn(url, { ...init, headers });

    if (response.status === 401) {
      await this.refresh();
      const newToken = await this.getAccessToken();
      headers.set("Authorization", `Bearer ${newToken}`);
      response = await this.fetchFn(url, { ...init, headers });
    }

    return response;
  }
}
