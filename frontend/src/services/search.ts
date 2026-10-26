import { api } from "@/lib/axios";
import type { SemanticSearchResponse } from "@/types/search";

export async function searchVideo(
  videoId: number,
  query: string,
  topK = 5,
): Promise<SemanticSearchResponse> {
  const { data } = await api.post<SemanticSearchResponse>(`/search/videos/${videoId}`, {
    query,
    top_k: topK,
  });
  return data;
}
