import { api } from "@/lib/axios";
import type { Chapter } from "@/types/chapter";

export async function getChapters(videoId: number): Promise<Chapter[]> {
  const { data } = await api.get<Chapter[]>(`/videos/${videoId}/chapters`);
  return data;
}
