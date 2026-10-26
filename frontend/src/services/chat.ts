import { api } from "@/lib/axios";
import { API_V1_URL } from "@/lib/constants";
import { readSseEvents } from "@/lib/sse";
import { getToken } from "@/lib/token";
import type { ChatHistoryEntry, RagResult } from "@/types/chat";
import type { SearchResult } from "@/types/search";

/**
 * Thrown by askVideoStream when the stream couldn't be opened at all
 * (network error, non-2xx status, no body) - nothing has been shown
 * to the user yet, so the caller can safely fall back to the regular
 * askVideo request, which also reports the real error properly
 * (401 → sign-in redirect, 404, 429...). Identified by `code`.
 */
export const STREAM_UNAVAILABLE = "STREAM_UNAVAILABLE";

function streamUnavailable(reason: string): Error & { code: string } {
  return Object.assign(new Error(`Answer streaming unavailable: ${reason}`), { code: STREAM_UNAVAILABLE });
}

export interface AskStreamHandlers {
  /** The chunks the answer is grounded in - sent before the first token. */
  onSources?: (sources: SearchResult[]) => void;
  /** The next piece of the answer text. */
  onToken: (text: string) => void;
  signal?: AbortSignal;
}

/**
 * Streaming variant of askVideo (POST /search/videos/{id}/rag/stream,
 * Server-Sent Events): calls `onSources`, then `onToken` for each piece
 * of the answer as the model writes it, and resolves with the final
 * RagResult - the same shape askVideo returns. A `generation_failed`
 * final status means the model failed mid-answer; discard the tokens.
 *
 * Rejects with code STREAM_UNAVAILABLE if the stream never opened (see
 * above), or with a plain Error if it broke off mid-answer.
 */
export async function askVideoStream(
  videoId: number,
  query: string,
  handlers: AskStreamHandlers,
  topK = 5,
): Promise<RagResult> {
  const token = getToken();
  let response: Response;
  try {
    response = await fetch(`${API_V1_URL}/search/videos/${videoId}/rag/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ query, top_k: topK }),
      signal: handlers.signal,
    });
  } catch (error) {
    if (handlers.signal?.aborted) throw error;
    throw streamUnavailable("network error");
  }

  if (!response.ok || !response.body) {
    throw streamUnavailable(`HTTP ${response.status}`);
  }

  let final: RagResult | null = null;
  for await (const frame of readSseEvents(response.body)) {
    const payload = JSON.parse(frame.data);
    if (frame.event === "sources") handlers.onSources?.(payload.sources as SearchResult[]);
    else if (frame.event === "token") handlers.onToken(payload.text as string);
    else if (frame.event === "done") final = payload as RagResult;
  }

  if (!final) {
    throw new Error("The answer was cut off before it finished. Please try again.");
  }
  return final;
}

/**
 * Video-scoped RAG question answering (see docs/api/rest_api.md,
 * Search & RAG section). Retrieval/generation is stateless per call —
 * no conversation id, nothing fed back in — but the backend now
 * records a genuinely answered turn server-side, so it can be
 * replayed later via getChatHistory below.
 */
export async function askVideo(videoId: number, query: string, topK = 5): Promise<RagResult> {
  const { data } = await api.post<RagResult>(`/search/videos/${videoId}/rag`, {
    query,
    top_k: topK,
  });
  return data;
}

/** This user's own past answered turns for the video, oldest first. */
export async function getChatHistory(videoId: number): Promise<ChatHistoryEntry[]> {
  const { data } = await api.get<ChatHistoryEntry[]>(`/videos/${videoId}/chat-history`);
  return data;
}
