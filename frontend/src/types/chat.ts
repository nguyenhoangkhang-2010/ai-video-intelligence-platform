import type { SearchResult } from "@/types/search";

/**
 * Matches backend app/schemas/rag.py::RAGResult exactly — these are
 * the only four states that exist; nothing is stateful, no
 * conversation is persisted server-side (see docs/api/rest_api.md,
 * Search & RAG section). Client-side chat history is
 * session/component-local only, never implying a saved conversation.
 */
export type RagStatus = "answered" | "empty_query" | "no_embeddings" | "no_relevant_chunks";

export interface RagResult {
  video_id: number;
  query: string;
  status: RagStatus;
  answer: string | null;
  sources: SearchResult[];
}

/** A single turn in the client-local (not persisted) chat transcript. */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: RagStatus;
  sources?: SearchResult[];
  error?: string;
  pending?: boolean;
}
