/**
 * Matches backend app/schemas/search.py. `distance` is a raw FAISS L2
 * distance (lower = closer) — never exposed as a fabricated
 * "similarity score" or percentage the backend doesn't compute.
 */

export interface SearchResult {
  vector_id: string;
  video_id: number;
  chunk_index: number;
  chunk_text: string;
  distance: number;
  /** Where in the video this chunk was spoken (seconds); null for videos processed before chunk times were stored. */
  start_time?: number | null;
  end_time?: number | null;
  /** "speech" = said in the video; "visual" = shown on screen (read from keyframes). */
  source?: "speech" | "visual";
}

export interface SemanticSearchResponse {
  video_id: number;
  query: string;
  results: SearchResult[];
}
