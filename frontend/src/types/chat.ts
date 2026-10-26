import type { SearchResult } from "@/types/search";

/**
 * Matches backend app/schemas/rag.py::RAGStatus exactly — these are
 * the only five states that exist, including `generation_failed`
 * (retrieval succeeded but the LLM call itself failed — set by
 * app/pipelines/rag_pipeline.py when it catches an LLMError).
 * Retrieval/generation itself stays stateless (no prior turn is fed
 * back into a later call); only a genuinely `answered` turn is
 * additionally recorded server-side to `ChatHistory` for later replay
 * (see useChat.ts and docs/api/rest_api.md, Search & RAG section).
 */
export type RagStatus =
  | "answered"
  | "empty_query"
  | "no_embeddings"
  | "no_relevant_chunks"
  | "generation_failed";

export interface RagResult {
  video_id: number;
  query: string;
  status: RagStatus;
  answer: string | null;
  sources: SearchResult[];
}

/** Matches backend app/schemas/chat_history.py::ChatHistoryRead — one persisted, previously-answered turn. */
export interface ChatHistoryEntry {
  id: number;
  user_id: number;
  video_id: number;
  question: string;
  answer: string;
  sources: SearchResult[];
  created_at: string;
}

/** A single turn in the chat transcript — seeded from persisted ChatHistoryEntry rows on load, then appended to locally as new turns are sent (see useChat.ts). */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  status?: RagStatus;
  sources?: SearchResult[];
  error?: string;
  /** Waiting for the first word of the answer (retrieval + model warm-up). */
  pending?: boolean;
  /** The answer is arriving word by word; `content` holds what's arrived so far. */
  streaming?: boolean;
}
