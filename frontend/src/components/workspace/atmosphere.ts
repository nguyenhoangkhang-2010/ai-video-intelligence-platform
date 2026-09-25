import type { WorkspaceSection } from "@/components/workspace/sections";

export type AtmosphereTone = "primary" | "signal" | "secondary" | "neutral";

/**
 * A subtle per-mode color identity behind the active panel — not a
 * strong background change, a very low-opacity radial tint (see
 * ATMOSPHERE_OPACITY below) using the same three semantic accents
 * already used everywhere else (primary/cobalt, signal/cyan,
 * secondary/violet). Transcript stays neutral (no tint) since its own
 * reading typography is the point, not an accent wash behind it.
 */
export const SECTION_ATMOSPHERE: Record<WorkspaceSection, AtmosphereTone> = {
  overview: "primary",
  chapters: "primary",
  transcript: "neutral",
  summary: "secondary",
  translation: "secondary",
  chat: "signal",
  search: "signal",
  quiz: "secondary",
  flashcards: "secondary",
};

const ATMOSPHERE_VAR: Record<Exclude<AtmosphereTone, "neutral">, string> = {
  primary: "--color-accent",
  signal: "--color-ai",
  secondary: "--color-atmosphere",
};

/** A CSS radial-gradient background value for the given mode, or `undefined` for "neutral" (no tint). */
export function atmosphereGradient(tone: AtmosphereTone): string | undefined {
  if (tone === "neutral") return undefined;
  const cssVar = ATMOSPHERE_VAR[tone];
  return `radial-gradient(ellipse 640px 420px at 100% 0%, rgb(var(${cssVar}) / 0.07), transparent 65%)`;
}
