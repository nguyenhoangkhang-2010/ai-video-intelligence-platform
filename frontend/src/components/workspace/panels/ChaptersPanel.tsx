"use client";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useChapters } from "@/hooks/useChapters";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { cn, formatTimecode } from "@/lib/utils";
import type { VideoStatus } from "@/types/video";

/**
 * "Narrative map" — a full-width proportional timeline is the primary
 * object (not a small strip above a list); the active chapter reads
 * as a large "now" card below it, and the full ordered list is a
 * compact reference underneath that. All positions/durations are
 * `end_time - start_time` from the real Chapter records.
 */
export function ChaptersPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const chapters = useChapters(videoId, videoStatus);
  const player = useVideoPlayer();

  if (chapters.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (chapters.isError) {
    return <ErrorState error={toApiError(chapters.error)} onRetry={() => chapters.refetch()} compact />;
  }

  if (!chapters.data || chapters.data.length === 0) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <div className="flex flex-col items-center gap-4 py-4">
          <ProcessingState
            icon="chapters"
            title="Chapters are being detected…"
            description="This updates automatically the moment they're ready — no need to refresh."
            compact
          />
        </div>
      );
    }
    return (
      <div className="flex flex-col items-center gap-4 py-4">
        <EmptyState
          icon="chapters"
          title="No chapters detected"
          description="Chapter detection is best-effort — short or single-topic videos may not produce any."
          compact
        />
      </div>
    );
  }

  const spanEnd = chapters.data[chapters.data.length - 1]?.end_time ?? 0;
  const activeIndex = chapters.data.findIndex(
    (chapter) => player.currentTime >= chapter.start_time && player.currentTime < chapter.end_time,
  );
  const active = activeIndex >= 0 ? chapters.data[activeIndex] : null;

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="chapters"
        label="Narrative map"
        meta={
          <span>
            {chapters.data.length} chapter{chapters.data.length === 1 ? "" : "s"}
          </span>
        }
      />

      <div className="flex-1 overflow-y-auto p-5 sm:p-6">
        {/* Full-width proportional timeline - the primary object. */}
        {/* Segments grow in proportion to their duration (flex-grow, not
            % widths, so gaps and the minimum width never overflow the
            row). Hover details open below the bar: above it they were
            clipped by this scroll container under the panel header. */}
        {spanEnd > 0 && (
          <div className="flex w-full gap-1">
            {chapters.data.map((chapter, index) => {
              const isActive = index === activeIndex;
              const duration = Math.max(0, chapter.end_time - chapter.start_time);
              const progress = isActive && duration > 0 ? ((player.currentTime - chapter.start_time) / duration) * 100 : 0;
              return (
                <button
                  key={chapter.id}
                  type="button"
                  onClick={() => player.seek(chapter.start_time)}
                  aria-label={`${chapter.title}, ${formatTimecode(chapter.start_time)}`}
                  aria-current={isActive ? "true" : undefined}
                  style={{ flexGrow: Math.max(duration, spanEnd * 0.01), flexBasis: 0 }}
                  className="group/marker relative min-w-[14px]"
                >
                  <span
                    className={cn(
                      "relative flex h-14 flex-col justify-between overflow-hidden rounded-md border px-2 py-1.5 text-left transition-colors duration-fast",
                      isActive
                        ? "border-accent bg-accent-muted"
                        : "border-border bg-surface-sunken group-hover/marker:border-border-strong group-hover/marker:bg-surface-hover",
                    )}
                  >
                    {isActive && (
                      <span aria-hidden className="absolute inset-y-0 left-0 bg-accent/20" style={{ width: `${Math.min(100, Math.max(0, progress))}%` }} />
                    )}
                    <span className={cn("relative font-mono text-[10px] leading-none", isActive ? "text-accent" : "text-text-muted")}>
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <span className="relative truncate font-mono text-[10px] leading-none text-text-secondary">
                      {formatTimecode(chapter.start_time)}
                    </span>
                  </span>
                  <span
                    className={cn(
                      "pointer-events-none absolute top-full z-dropdown mt-2 hidden w-max max-w-[240px] rounded-md border border-border-strong bg-surface-elevated px-2.5 py-1.5 text-left shadow-md group-hover/marker:block",
                      index === 0 ? "left-0" : index === chapters.data.length - 1 ? "right-0" : "left-1/2 -translate-x-1/2",
                    )}
                  >
                    <span className="block truncate text-caption font-medium text-text-primary">{chapter.title}</span>
                    <span className="block font-mono text-[10px] text-text-muted">
                      {formatTimecode(chapter.start_time)} – {formatTimecode(chapter.end_time)}
                    </span>
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* "Now" — the active chapter, large. */}
        <div className="mt-6 min-h-[88px] rounded-lg border border-border bg-surface p-5">
          {active ? (
            <>
              <p className="index-label text-accent">
                Now — {formatTimecode(active.start_time)}
              </p>
              <p className="mt-1.5 text-heading-sm font-medium text-text-primary">{active.title}</p>
              {active.summary && <p className="mt-1.5 text-body-sm leading-relaxed text-text-secondary">{active.summary}</p>}
            </>
          ) : (
            <p className="text-body-sm text-text-muted">Play the video, or select a chapter below, to see it here.</p>
          )}
        </div>

        {/* Compact reference list. */}
        <ol className="mt-6 flex flex-col divide-y divide-border">
          {chapters.data.map((chapter, index) => {
            const isActive = index === activeIndex;
            const duration = Math.max(0, chapter.end_time - chapter.start_time);
            return (
              <li key={chapter.id}>
                <button
                  type="button"
                  onClick={() => player.seek(chapter.start_time)}
                  className={cn(
                    "flex w-full items-center gap-3 py-2.5 text-left transition-colors duration-fast",
                    isActive ? "text-text-primary" : "text-text-secondary hover:text-text-primary",
                  )}
                >
                  <span className={cn("shrink-0 font-mono text-caption", isActive ? "text-accent" : "text-text-muted")}>
                    {formatTimecode(chapter.start_time)}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-body-sm font-medium">{chapter.title}</span>
                  {duration > 0 && (
                    <span className="shrink-0 font-mono text-caption text-text-muted">{formatTimecode(duration)}</span>
                  )}
                </button>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
