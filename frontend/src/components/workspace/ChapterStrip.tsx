"use client";

import { Icon } from "@/components/ui/Icon";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { formatTimecode } from "@/lib/utils";
import type { Chapter } from "@/types/chapter";

/** Compact "now playing" chapter indicator with prev/next navigation, directly under the player. */
export function ChapterStrip({ chapters }: { chapters: Chapter[] }) {
  const player = useVideoPlayer();

  if (chapters.length === 0) return null;

  const activeIndex = chapters.findIndex(
    (chapter) => player.currentTime >= chapter.start_time && player.currentTime < chapter.end_time,
  );
  const current = activeIndex >= 0 ? chapters[activeIndex] : null;
  const previous = activeIndex > 0 ? chapters[activeIndex - 1] : null;
  const next = activeIndex >= 0 && activeIndex < chapters.length - 1 ? chapters[activeIndex + 1] : chapters[0];

  return (
    <div className="flex items-center gap-2 rounded-md border border-border bg-surface px-2 py-1.5">
      <button
        type="button"
        onClick={() => previous && player.seek(previous.start_time)}
        disabled={!previous}
        aria-label="Previous chapter"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-text-muted enabled:hover:bg-surface-hover enabled:hover:text-text-primary disabled:opacity-30"
      >
        <Icon name="chevron-left" size={15} />
      </button>

      <div className="min-w-0 flex-1 text-center">
        {current ? (
          <p className="truncate text-caption text-text-secondary">
            <span className="font-mono text-text-muted">{formatTimecode(current.start_time)}</span>
            {"  "}
            {current.title}
          </p>
        ) : (
          <p className="text-caption text-text-muted">No active chapter</p>
        )}
      </div>

      <button
        type="button"
        onClick={() => next && player.seek(next.start_time)}
        disabled={!next}
        aria-label="Next chapter"
        className="flex h-6 w-6 shrink-0 items-center justify-center rounded text-text-muted enabled:hover:bg-surface-hover enabled:hover:text-text-primary disabled:opacity-30"
      >
        <Icon name="chevron-right" size={15} />
      </button>
    </div>
  );
}
