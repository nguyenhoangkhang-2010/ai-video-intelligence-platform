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
}

export interface SemanticSearchResponse {
  video_id: number;
  query: string;
  results: SearchResult[];
}
