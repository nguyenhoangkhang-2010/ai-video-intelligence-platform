import { api } from "@/lib/axios";
import type { ChatHistoryEntry, RagResult } from "@/types/chat";

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
