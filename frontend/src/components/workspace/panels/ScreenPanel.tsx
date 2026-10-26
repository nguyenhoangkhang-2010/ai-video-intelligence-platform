"use client";

import { useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { BaseBadge, type Tone } from "@/components/ui/StatusBadge";
import { SeekButton } from "@/components/video/SeekButton";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useMediaToken } from "@/hooks/useVideos";
import { useOptionalVideoPlayer } from "@/hooks/useVideoPlayer";
import { useVisualSegments } from "@/hooks/useVisualSegments";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { getVisualFrameUrl } from "@/services/visual";
import type { VideoStatus } from "@/types/video";
import type { VisualRelation, VisualSegment } from "@/types/visual";

const RELATION: Record<VisualRelation, { label: string; tone: Tone; hint: string }> = {
  illustrates: {
    label: "Matches speech",
    tone: "ai",
    hint: "What is shown matches what was being said at the time.",
  },
  unrelated: {
    label: "B-roll",
    tone: "neutral",
    hint: "Footage that doesn't match what was being said - e.g. a voice-over over other scenes.",
  },
  "no-speech": {
    label: "No speech",
    tone: "info",
    hint: "Nothing was said while this was on screen.",
  },
};

/**
 * "On screen" — what the video SHOWS, read from its keyframes by a
 * vision model: text on screen (slides, captions, code) and a short
 * description of the picture, each with the moment it appears. Kept
 * apart from the transcript on purpose: shown and said are two
 * different sources, and each card says how they relate.
 */
export function ScreenPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const segments = useVisualSegments(videoId, videoStatus);
  const anyFrame = segments.data?.some((segment) => segment.has_frame) ?? false;
  const mediaToken = useMediaToken(videoId, anyFrame);

  if (segments.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-5">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-24 w-full" />
        ))}
      </div>
    );
  }

  if (segments.isError) {
    return <ErrorState error={toApiError(segments.error)} onRetry={() => segments.refetch()} compact />;
  }

  if (!segments.data || segments.data.length === 0) {
    return (
      <div className="flex flex-col items-center gap-4 py-4">
        {isTerminalVideoStatus(videoStatus) ? (
          <EmptyState
            icon="eye"
            title="Nothing read from the screen"
            description="Visual analysis is best-effort: it needs the vision model in Ollama, and a video with no on-screen content may have nothing to show."
            compact
          />
        ) : (
          <ProcessingState
            icon="eye"
            title="Reading the screen…"
            description="Keyframes are being analysed. This updates automatically."
            compact
          />
        )}
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="eye"
        label="On screen"
        meta={
          <span>
            {segments.data.length} scene{segments.data.length === 1 ? "" : "s"}
          </span>
        }
      />
      <ol className="flex-1 divide-y divide-border overflow-y-auto">
        {segments.data.map((segment) => (
          <ScreenRow key={segment.id} segment={segment} videoId={videoId} mediaToken={mediaToken.data} />
        ))}
      </ol>
    </div>
  );
}

function ScreenRow({
  segment,
  videoId,
  mediaToken,
}: {
  segment: VisualSegment;
  videoId: number;
  mediaToken: string | undefined;
}) {
  const [imageFailed, setImageFailed] = useState(false);
  const player = useOptionalVideoPlayer();
  const isActive =
    player !== null && player.currentTime >= segment.start_time && player.currentTime < segment.end_time;
  const relation = RELATION[segment.relation];
  const showImage = segment.has_frame && mediaToken && !imageFailed;

  return (
    <li
      aria-current={isActive ? "true" : undefined}
      className={cn("flex gap-4 px-5 py-4 sm:px-6", isActive && "bg-accent-muted")}
    >
      <div className="relative aspect-video w-32 shrink-0 overflow-hidden rounded-md border border-border bg-surface-sunken sm:w-40">
        {showImage && (
          // Token-bearing URL, same reasoning as VideoThumbnail: not a fit for next/image.
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={getVisualFrameUrl(videoId, segment.id, mediaToken)}
            alt={segment.description || "Keyframe"}
            loading="lazy"
            onError={() => setImageFailed(true)}
            className="absolute inset-0 h-full w-full object-cover"
          />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <div className="mb-1.5 flex flex-wrap items-center gap-2">
          <SeekButton seconds={segment.start_time} />
          <span title={relation.hint}>
            <BaseBadge tone={relation.tone} label={relation.label} />
          </span>
        </div>
        {segment.on_screen_text && (
          <p className="mb-1.5 whitespace-pre-line border-l-2 border-accent pl-2.5 font-mono text-caption leading-relaxed text-text-primary">
            {segment.on_screen_text}
          </p>
        )}
        {segment.description && (
          <p className="text-body-sm leading-relaxed text-text-secondary">{segment.description}</p>
        )}
      </div>
    </li>
  );
}
