/**
 * Re-exports the shared HTTP client (see src/lib/axios.ts, where auth
 * injection and error normalization actually live) so every service
 * module in this directory can import it from a sibling path.
 */
export { api, toApiError } from "@/lib/axios";
export type { ApiError } from "@/lib/axios";
