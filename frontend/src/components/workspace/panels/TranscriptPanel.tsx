"use client";

import { useMemo, useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Highlight } from "@/components/ui/Highlight";
import { Icon } from "@/components/ui/Icon";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useTranscript } from "@/hooks/useTranscript";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { cn, formatNumber } from "@/lib/utils";
import type { VideoStatus } from "@/types/video";

/**
 * Full transcript text only — the backend does not provide
 * timestamped segments (see docs/api/rest_api.md, Transcript
 * section), so no per-sentence timestamp is invented here; the
 * left-margin index is the paragraph's ordinal position, not a time.
 * Chapter navigation (real start_time data) lives in the Chapters
 * panel.
 */
export function TranscriptPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const transcript = useTranscript(videoId, videoStatus);
  const [filter, setFilter] = useState("");

  const paragraphs = useMemo(() => {
    if (!transcript.data) return [];
    return transcript.data.text
      .split(/\n+/)
      .map((paragraph) => paragraph.trim())
      .filter(Boolean);
  }, [transcript.data]);

  const matchCount = useMemo(() => {
    const trimmed = filter.trim().toLowerCase();
    if (!trimmed) return 0;
    return paragraphs.reduce((count, paragraph) => {
      const occurrences = paragraph.toLowerCase().split(trimmed).length - 1;
      return count + occurrences;
    }, 0);
  }, [paragraphs, filter]);

  if (transcript.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-5">
        <Skeleton className="h-4 w-1/2" />
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  const status = (transcript.error as { response?: { status?: number } } | null)?.response?.status;
  if (transcript.isError && status !== 404) {
    return <ErrorState error={toApiError(transcript.error)} onRetry={() => transcript.refetch()} compact />;
  }

  if (transcript.isError || !transcript.data) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <ProcessingState
          icon="transcript"
          title="Transcript is being generated…"
          description="This updates automatically the moment transcription finishes — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="transcript"
        title="No transcript available"
        description="Processing finished without producing a transcript for this video."
      />
    );
  }

  const { language, word_count, text } = transcript.data;

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="transcript"
        label="Transcript"
        meta={
          <span className="flex items-center gap-2">
            <span className="uppercase tracking-wide">{language}</span>
            <span aria-hidden="true">·</span>
            <span className="font-mono">{formatNumber(word_count)} words</span>
          </span>
        }
        actions={
          <>
            <div className="relative">
              <Icon
                name="search"
                size={13}
                className="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-text-muted"
              />
              <input
                type="text"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
                placeholder="Find in transcript"
                aria-label="Find in transcript"
                className="h-7 w-44 rounded border border-border-strong bg-surface-sunken pl-7 pr-2 text-caption text-text-primary placeholder:text-text-muted transition-colors duration-fast focus-visible:outline-2 focus-visible:outline-accent"
              />
            </div>
            {filter.trim() && (
              <span className="whitespace-nowrap text-caption text-text-muted">
                {matchCount} match{matchCount === 1 ? "" : "es"}
              </span>
            )}
          </>
        }
      />

      <div className="flex-1 overflow-y-auto px-6 py-6 sm:px-10">
        <div className="relative mx-auto max-w-[68ch]">
          {/* A continuous reading rail, not per-paragraph numbers - this is one linear stream, not a numbered list. */}
          <div className="absolute bottom-0 left-0 top-1 w-px bg-border" aria-hidden="true" />
          <div className="flex flex-col gap-5 pl-6">
            {paragraphs.map((paragraph, index) => {
              const hasMatch = Boolean(filter.trim()) && paragraph.toLowerCase().includes(filter.trim().toLowerCase());
              return (
                <p
                  key={index}
                  className={cn(
                    "text-body-lg leading-[1.75] text-text-secondary transition-colors duration-base",
                    hasMatch && "-ml-[13px] border-l-2 border-accent pl-3 text-text-primary",
                  )}
                >
                  <Highlight text={paragraph} query={filter} />
                </p>
              );
            })}
            {paragraphs.length === 0 && <p className="text-body-lg leading-[1.75] text-text-secondary">{text}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
