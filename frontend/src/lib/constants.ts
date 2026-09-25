/**
 * Central, environment-driven constants. Nothing here hardcodes a
 * backend capability that doesn't exist — see docs/api/rest_api.md
 * (repository root) for the API this frontend is built against.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

/** Everything under /api/v1 on the backend. */
export const API_V1_URL = `${API_BASE_URL}/api/v1`;

/** localStorage key for the JWT access token. */
export const AUTH_TOKEN_STORAGE_KEY = "aivip_access_token";

/**
 * Processing status polling interval while a video is uploaded/
 * processing. The backend has no push/streaming channel for job
 * progress (Phase 13 confirmed no WebSocket infrastructure), so
 * polling is the only available mechanism.
 */
export const PROCESSING_POLL_INTERVAL_MS = 3000;

/** Terminal Video.status values — matches app/services/video.py exactly. */
export const TERMINAL_VIDEO_STATUSES = ["processed", "failed"] as const;

/**
 * True once the pipeline has reached a terminal state for this video
 * (processed or failed) — false while it's still "uploaded"/
 * "processing". Every per-artifact hook (transcript/summary/
 * translation/quiz/flashcards/chapters) uses this to decide whether
 * to keep polling and every panel uses it to decide whether an empty
 * result means "still being generated" or "genuinely not produced" -
 * see hooks/useVideos.ts::useVideo for the original pattern this
 * mirrors.
 */
export function isTerminalVideoStatus(status: string): boolean {
  return (TERMINAL_VIDEO_STATUSES as readonly string[]).includes(status);
}

export const ROUTES = {
  login: "/login",
  register: "/register",
  library: "/library",
  upload: "/library/upload",
  video: (id: number | string) => `/videos/${id}`,
  account: "/account",
} as const;
