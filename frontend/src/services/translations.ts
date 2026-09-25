import { api } from "@/lib/axios";
import type { Translation } from "@/types/translation";

export async function getTranslations(videoId: number): Promise<Translation[]> {
  const { data } = await api.get<Translation[]>(`/translations/video/${videoId}`);
  return data;
}
