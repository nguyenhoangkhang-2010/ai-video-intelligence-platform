import { AUTH_TOKEN_STORAGE_KEY } from "@/lib/constants";

/**
 * The backend issues a JWT access token with no refresh token (see
 * docs/api/rest_api.md, Authentication section) — the client simply
 * holds it in localStorage until it expires or the user logs out.
 * Centralized here so no other module touches localStorage directly.
 */

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(AUTH_TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(AUTH_TOKEN_STORAGE_KEY);
}
