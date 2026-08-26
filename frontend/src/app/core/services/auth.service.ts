import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, tap } from 'rxjs';
import { AuthTokens, IliasCredential, User } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly baseUrl = 'http://localhost:8000/api';
  private readonly ACCESS_KEY = 'access_token';
  private readonly REFRESH_KEY = 'refresh_token';

  constructor(private http: HttpClient) {}

  login(email: string, password: string): Observable<AuthTokens> {
    return this.http
      .post<AuthTokens>(`${this.baseUrl}/auth/login/`, { email, password })
      .pipe(
        tap((tokens) => {
          localStorage.setItem(this.ACCESS_KEY, tokens.access);
          localStorage.setItem(this.REFRESH_KEY, tokens.refresh);
        })
      );
  }

  register(
    email: string,
    password: string,
    firstName: string,
    lastName: string
  ): Observable<User> {
    return this.http.post<User>(`${this.baseUrl}/auth/register/`, {
      email,
      password,
      first_name: firstName,
      last_name: lastName,
    });
  }

  logout(): void {
    localStorage.removeItem(this.ACCESS_KEY);
    localStorage.removeItem(this.REFRESH_KEY);
  }

  isLoggedIn(): boolean {
    return !!localStorage.getItem(this.ACCESS_KEY);
  }

  getToken(): string | null {
    return localStorage.getItem(this.ACCESS_KEY);
  }

  getProfile(): Observable<User> {
    return this.http.get<User>(`${this.baseUrl}/auth/profile/`);
  }

  updateProfile(data: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${this.baseUrl}/auth/profile/`, data);
  }

  saveIliasCredentials(iliasUsername: string): Observable<IliasCredential> {
    return this.http.post<IliasCredential>(
      `${this.baseUrl}/auth/ilias-credentials/`,
      { ilias_username: iliasUsername, ilias_password: '' }
    );
  }

  getIliasCredentials(): Observable<IliasCredential> {
    return this.http.get<IliasCredential>(
      `${this.baseUrl}/auth/ilias-credentials/`
    );
  }
}
