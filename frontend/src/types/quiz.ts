/**
 * Matches backend app/schemas/quiz.py. `options` is a comma-joined
 * string for multiple_choice questions, null otherwise (see
 * lib/utils.ts::parseQuizOptions). Read-only: there is no
 * submit/score/attempt-history endpoint.
 */

export type QuizType = "multiple_choice" | "true_false" | "short_answer";

export interface Quiz {
  id: number;
  video_id: number;
  type: QuizType;
  question: string;
  answer: string;
  options: string | null;
}
