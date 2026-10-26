import { api } from "@/lib/axios";
import type { Quiz } from "@/types/quiz";

export async function getQuizzes(videoId: number): Promise<Quiz[]> {
  const { data } = await api.get<Quiz[]>(`/videos/${videoId}/quizzes`);
  return data;
}
