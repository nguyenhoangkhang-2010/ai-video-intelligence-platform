/** Matches backend app/schemas/transcript.py. */

/** One timed piece of speech, in video seconds. */
export interface TranscriptSegment {
  start: number;
  end: number;
  text: string;
  speaker?: string | null;
}

export interface Transcript {
  id: number;
  video_id: number;
  language: string;
  text: string;
  word_count: number;
  created_at: string;
  /** Whisper's timed segments; null for transcripts saved before these were stored. */
  segments?: TranscriptSegment[] | null;
  /** "visual" when the video had no speech and this was built from what is on screen. */
  source?: "speech" | "visual";
}
