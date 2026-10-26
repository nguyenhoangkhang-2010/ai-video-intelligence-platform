/**
 * Matches backend app/schemas/visual_segment.py::VisualSegmentRead.
 *
 * `relation` says how the picture relates to what was being said
 * while it was on screen (BGE-M3 similarity, see ai/vision/segments.py):
 * "illustrates" (slides matching the talk), "unrelated" (b-roll under a
 * voice-over), or "no-speech" (nothing was said then).
 */
export type VisualRelation = "illustrates" | "unrelated" | "no-speech";

export interface VisualSegment {
  id: number;
  video_id: number;
  start_time: number;
  end_time: number;
  on_screen_text: string;
  description: string;
  speech_similarity: number | null;
  relation: VisualRelation;
  has_frame: boolean;
}
