/** Matches backend app/schemas/transcript.py. */

export interface Transcript {
  id: number;
  video_id: number;
  language: string;
  text: string;
  word_count: number;
  created_at: string;
}
