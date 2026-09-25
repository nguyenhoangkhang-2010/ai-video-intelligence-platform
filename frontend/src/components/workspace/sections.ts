import type { IconName } from "@/components/ui/Icon";

export type WorkspaceSection =
  | "overview"
  | "transcript"
  | "summary"
  | "translation"
  | "search"
  | "chat"
  | "quiz"
  | "chapters"
  | "flashcards";

interface SectionDef {
  id: WorkspaceSection;
  label: string;
  icon: IconName;
  /**
   * "ai" marks a section whose content/interaction is itself AI-driven
   * (retrieval/generation on demand, the Ask group) - cyan Signal.
   * "atmosphere" marks the Study group specifically - a genuinely
   * different kind of engagement (focused review) from either
   * Pearl's default actions or Signal's live AI activity - violet.
   */
  tone?: "ai" | "atmosphere";
}

export const WORKSPACE_SECTIONS: SectionDef[] = [
  { id: "overview", label: "Overview", icon: "video" },
  { id: "chapters", label: "Chapters", icon: "chapters" },
  { id: "transcript", label: "Transcript", icon: "transcript" },
  { id: "summary", label: "Summary", icon: "summary" },
  { id: "translation", label: "Translation", icon: "translate" },
  { id: "chat", label: "AI Chat", icon: "chat", tone: "ai" },
  { id: "search", label: "Search", icon: "search", tone: "ai" },
  { id: "quiz", label: "Quiz", icon: "quiz", tone: "atmosphere" },
  { id: "flashcards", label: "Flashcards", icon: "flashcard", tone: "atmosphere" },
];

/**
 * The mode bar groups by mental model, not by page type — watch the
 * source itself, understand what the pipeline distilled from it, ask
 * its live intelligence layer a question, study it. Every mode is
 * always visible in this bar (see ModeBar) — never hidden behind a
 * dropdown, a drawer toggle, or an unlabeled icon row.
 */
export const WORKSPACE_SECTION_GROUPS: Array<{ label: string; ids: WorkspaceSection[] }> = [
  { label: "Watch", ids: ["overview", "chapters"] },
  { label: "Understand", ids: ["transcript", "summary", "translation"] },
  { label: "Ask", ids: ["chat", "search"] },
  { label: "Study", ids: ["quiz", "flashcards"] },
];
