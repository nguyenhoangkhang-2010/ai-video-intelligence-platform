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
        <ProcessingState
          icon="chapters"
          title="Chapters are being detected…"
          description="This updates automatically the moment they're ready — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="chapters"
        title="No chapters detected"
        description="Chapter detection is best-effort — short or single-topic videos may not produce any."
      />
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
        {spanEnd > 0 && (
          <div className="flex w-full gap-[3px]">
            {chapters.data.map((chapter, index) => {
              const isActive = index === activeIndex;
              const width = ((chapter.end_time - chapter.start_time) / spanEnd) * 100;
              return (
                <button
                  key={chapter.id}
                  type="button"
                  onClick={() => player.seek(chapter.start_time)}
                  style={{ width: `${Math.max(width, 2)}%` }}
                  className="group/marker relative shrink-0"
                >
                  <span
                    className={cn(
                      "block h-12 rounded-md transition-[background-color,transform] duration-fast",
                      isActive
                        ? "bg-accent"
                        : "bg-surface-elevated group-hover/marker:scale-y-105 group-hover/marker:bg-border-strong",
                    )}
                  />
                  <span className="pointer-events-none absolute -top-2 left-1/2 z-dropdown hidden w-max max-w-[220px] -translate-x-1/2 -translate-y-full rounded-md border border-border-strong bg-surface-elevated px-2.5 py-1.5 text-left shadow-md group-hover/marker:block">
                    <span className="block truncate text-caption font-medium text-text-primary">{chapter.title}</span>
                    <span className="block font-mono text-[10px] text-text-muted">{formatTimecode(chapter.start_time)}</span>
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
              <p className="text-label font-semibold uppercase tracking-wide text-accent">
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
