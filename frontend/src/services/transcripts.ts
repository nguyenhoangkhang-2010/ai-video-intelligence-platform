import { api } from "@/lib/axios";
import type { Transcript } from "@/types/transcript";

export async function getTranscript(videoId: number): Promise<Transcript> {
  const { data } = await api.get<Transcript>(`/transcripts/${videoId}`);
  return data;
}
