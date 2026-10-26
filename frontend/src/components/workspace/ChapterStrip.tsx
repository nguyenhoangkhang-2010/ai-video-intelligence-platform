"use client";

import { toRoman } from "@/components/dial/geometry";
import { Icon } from "@/components/ui/Icon";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { formatTimecode } from "@/lib/utils";
import type { Chapter } from "@/types/chapter";

/** "Now playing" chapter window with prev/next pushers, directly under the dial. */
export function ChapterStrip({ chapters }: { chapters: Chapter[] }) {
  const player = useVideoPlayer();

  if (chapters.length === 0) return null;

  const activeIndex = chapters.findIndex(
    (chapter) => player.currentTime >= chapter.start_time && player.currentTime < chapter.end_time,
  );
  const current = activeIndex >= 0 ? chapters[activeIndex] : null;
  const previous = activeIndex > 0 ? chapters[activeIndex - 1] : null;
  const next = activeIndex >= 0 && activeIndex < chapters.length - 1 ? chapters[activeIndex + 1] : chapters[0];

  const pusher =
    "flex h-9 w-9 shrink-0 items-center justify-center text-text-primary transition-colors duration-fast enabled:hover:bg-surface-hover disabled:text-text-disabled";

  return (
    <div className="flex items-stretch border border-text-primary/60 bg-surface-elevated">
      <button
        type="button"
        onClick={() => previous && player.seek(previous.start_time)}
        disabled={!previous}
        aria-label="Previous chapter"
        className={`${pusher} border-r border-text-primary/30`}
      >
        <Icon name="chevron-left" size={15} />
      </button>

      <div className="flex min-w-0 flex-1 items-center justify-center gap-3 px-3">
        {current ? (
          <>
            <span className="font-display text-body-sm font-semibold text-atmosphere">{toRoman(activeIndex + 1)}</span>
            <span className="font-mono text-caption text-text-muted">{formatTimecode(current.start_time)}</span>
            <span className="truncate text-body-sm text-text-primary">{current.title}</span>
          </>
        ) : (
          <span className="index-label text-text-muted">No active chapter</span>
        )}
      </div>

      <button
        type="button"
        onClick={() => next && player.seek(next.start_time)}
        disabled={!next}
        aria-label="Next chapter"
        className={`${pusher} border-l border-text-primary/30`}
      >
        <Icon name="chevron-right" size={15} />
      </button>
    </div>
  );
}
