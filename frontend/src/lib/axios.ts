import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";

import { API_V1_URL, ROUTES } from "@/lib/constants";
import { clearToken, getToken } from "@/lib/token";

/**
 * Single shared HTTP client for every backend call. Every service
 * module (see src/services/) imports this instead of constructing
 * its own axios instance, so auth injection and error normalization
 * happen in exactly one place.
 */
export const api = axios.create({
  baseURL: API_V1_URL,
});

api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

/**
 * Backend error shape (see docs/api/rest_api.md, "Error responses"):
 * `{"detail": "..."}` for most errors, `{"detail": [{...}, ...]}` for
 * 422 validation errors. Normalized here into one shape every caller
 * can rely on without re-parsing axios error internals.
 */
export interface ApiError {
  status: number | null;
  message: string;
  /** Present only for 422 validation errors, one entry per invalid field. */
  fieldErrors: Array<{ field: string; message: string }> | null;
}

export function toApiError(error: unknown): ApiError {
  if (!axios.isAxiosError(error)) {
    return {
      status: null,
      message: "Something unexpected happened. Please try again.",
      fieldErrors: null,
    };
  }

  const axiosError = error as AxiosError<{ detail?: unknown }>;

  if (!axiosError.response) {
    return {
      status: null,
      message:
        "Can't reach the server. Check your connection and try again.",
      fieldErrors: null,
    };
  }

  const { status, data } = axiosError.response;
  const detail = data?.detail;

  if (Array.isArray(detail)) {
    const fieldErrors = detail
      .map((entry) => {
        if (
          entry &&
          typeof entry === "object" &&
          "msg" in entry &&
          "loc" in entry &&
          Array.isArray((entry as { loc: unknown }).loc)
        ) {
          const loc = (entry as { loc: unknown[] }).loc;
          const field = String(loc[loc.length - 1] ?? "field");
          return { field, message: String((entry as { msg: unknown }).msg) };
        }
        return null;
      })
      .filter((entry): entry is { field: string; message: string } => entry !== null);

    return {
      status,
      message: fieldErrors[0]?.message ?? "Please check the highlighted fields.",
      fieldErrors: fieldErrors.length > 0 ? fieldErrors : null,
    };
  }

  return {
    status,
    message: typeof detail === "string" ? detail : defaultMessageFor(status),
    fieldErrors: null,
  };
}

function defaultMessageFor(status: number): string {
  switch (status) {
    case 401:
      return "You need to sign in again.";
    case 403:
      return "You don't have access to this.";
    case 404:
      return "We couldn't find that.";
    case 409:
      return "That already exists.";
    case 500:
      return "The server ran into a problem. Please try again.";
    default:
      return "Something went wrong. Please try again.";
  }
}

/**
 * Session expiry handling: a 401 from any *authenticated* endpoint
 * means the token is missing/invalid/expired, so the client clears
 * it and returns to login. A 401 from /auth/login itself is a normal
 * "wrong password" response, not a session expiry, and must not
 * trigger this — callers there read the ApiError instead.
 */
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const isAuthEndpoint = error.config?.url?.startsWith("/auth/");
    if (error.response?.status === 401 && !isAuthEndpoint) {
      clearToken();
      if (typeof window !== "undefined" && window.location.pathname !== ROUTES.login) {
        window.location.href = ROUTES.login;
      }
    }
    return Promise.reject(error);
  },
);
