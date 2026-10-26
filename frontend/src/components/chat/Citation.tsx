"use client";

import { useState } from "react";

import type { SearchResult } from "@/types/search";

/**
 * A numbered source reference chip — expands to show the real
 * grounding chunk text on demand. No seek-to-timestamp action here:
 * unlike Chapters (which have real start_time/end_time), a RAG
 * source is only ever `{vector_id, chunk_index, chunk_text,
 * distance}` — the API has no timestamp for a retrieved chunk, so
 * this never fakes one or implies a seek capability that doesn't
 * exist. Colored as AI evidence (cyan), not a generic UI accent.
 */
export function Citation({ index, source }: { index: number; source: SearchResult }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="inline-block">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        className="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-border-strong bg-surface-elevated px-1 font-mono text-[11px] text-text-secondary transition-colors duration-fast hover:border-ai-border hover:bg-ai-muted hover:text-ai"
      >
        {index}
      </button>
      {expanded && (
        <div className="mt-1.5 max-w-md animate-slide-up rounded border border-ai-border bg-surface-sunken p-2.5 text-caption leading-relaxed text-text-secondary">
          <span className="mb-1 block font-medium text-ai">Segment {source.chunk_index + 1}</span>
          {source.chunk_text}
        </div>
      )}
    </div>
  );
}
