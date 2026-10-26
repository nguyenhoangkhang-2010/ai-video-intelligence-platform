"use client";

import { useState } from "react";

import { SeekButton } from "@/components/video/SeekButton";
import { useOptionalVideoPlayer } from "@/hooks/useVideoPlayer";
import { formatTimecode } from "@/lib/utils";
import type { SearchResult } from "@/types/search";

/**
 * A numbered source reference chip. Expands to show the real grounding
 * chunk text and, when the chunk's time span is known (videos processed
 * after chunk times were stored), when it was said - with a button that
 * plays the video from that moment. Older videos have no span, so no
 * time is shown or implied.
 */
export function Citation({ index, source }: { index: number; source: SearchResult }) {
  const [expanded, setExpanded] = useState(false);
  const player = useOptionalVideoPlayer();
  const hasTime = source.start_time !== null && source.start_time !== undefined;

  return (
    <div className="inline-block">
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        aria-expanded={expanded}
        title={hasTime ? `Source ${index} · ${formatTimecode(source.start_time!)}` : `Source ${index}`}
        className="inline-flex h-5 min-w-5 items-center justify-center rounded-full border border-border-strong bg-surface-elevated px-1 font-mono text-[11px] text-text-secondary transition-colors duration-fast hover:border-ai hover:bg-ai-muted hover:text-ai"
      >
        {index}
      </button>
      {expanded && (
        <div className="mt-1.5 max-w-md animate-slide-up border border-ai/40 bg-surface-sunken p-2.5 text-caption leading-relaxed text-text-secondary">
          <span className="mb-1.5 flex flex-wrap items-center gap-2 font-medium text-ai">
            Segment {source.chunk_index + 1}
            {hasTime && (
              <span className="font-mono text-text-muted">
                {formatTimecode(source.start_time!)}
                {source.end_time !== null && source.end_time !== undefined && ` – ${formatTimecode(source.end_time)}`}
              </span>
            )}
            {hasTime && player && <SeekButton seconds={source.start_time} />}
            {source.source === "visual" && <span className="index-label text-accent">Shown on screen</span>}
          </span>
          {source.chunk_text}
        </div>
      )}
    </div>
  );
}
