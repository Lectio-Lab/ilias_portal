export interface User {
  email: string;
  first_name: string;
  last_name: string;
}

export interface IliasCredential {
  ilias_username: string;
  ilias_password?: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}
