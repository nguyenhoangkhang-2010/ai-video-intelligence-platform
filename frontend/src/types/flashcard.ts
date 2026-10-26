/** Matches backend app/schemas/flashcard.py. */

export interface Flashcard {
  id: number;
  video_id: number;
  question: string;
  answer: string;
  difficulty: string;
}
