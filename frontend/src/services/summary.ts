import { api } from "@/lib/axios";
import type { Summary } from "@/types/summary";

export async function getSummaries(videoId: number): Promise<Summary[]> {
  const { data } = await api.get<Summary[]>(`/summaries/video/${videoId}`);
  return data;
}
