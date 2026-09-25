import { api } from "@/lib/axios";
import type { MeetingResponse } from "@/types/meeting";

/** Aggregated video+jobs+transcript+summaries+translations+quizzes in one call. */
export async function getMeeting(videoId: number): Promise<MeetingResponse> {
  const { data } = await api.get<MeetingResponse>(`/meetings/${videoId}`);
  return data;
}
