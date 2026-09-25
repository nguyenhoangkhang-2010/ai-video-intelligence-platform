import { api } from "@/lib/axios";
import type { RagResult } from "@/types/chat";

/**
 * Video-scoped, stateless RAG question answering (see
 * docs/api/rest_api.md, Search & RAG section). No conversation id,
 * no history endpoint — every call is independent.
 */
export async function askVideo(videoId: number, query: string, topK = 5): Promise<RagResult> {
  const { data } = await api.post<RagResult>(`/search/videos/${videoId}/rag`, {
    query,
    top_k: topK,
  });
  return data;
}
