"use client";

import { useAccentSlotClaim } from "@/components/3d/workspace3d/AccentSlotContext";
import { statusBadgeHideNodes } from "@/components/3d/workspace3d/registry";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { BaseBadge, type Tone } from "@/components/ui/StatusBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import { Icon, type IconName } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Spinner";
import type { WorkspaceSection } from "@/components/workspace/sections";
import { useChapters } from "@/hooks/useChapters";
import { useFlashcards } from "@/hooks/useFlashcards";
import { useMeeting } from "@/hooks/useMeeting";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { toApiError } from "@/lib/axios";
import { cn, formatDate, formatTimecode, truncate, videoStatusLabel } from "@/lib/utils";
import type { Video } from "@/types/video";

interface OverviewPanelProps {
  video: Video;
  onNavigate: (section: WorkspaceSection) => void;
}

interface Capability {
  section: WorkspaceSection;
  icon: IconName;
  label: string;
  ready: boolean;
  count?: number;
}

/**
 * The video's own status only ever means "the whole pipeline hasn't
 * finished" — it says nothing about any single capability. Each
 * capability's tone is derived from its OWN data (present or not),
 * never gated behind video.status, so this stays accurate even for a
 * video that's still mid-pipeline (some stages can finish before
 * others) or one that finished with a legitimately empty result
 * (e.g. chapter detection is best-effort).
 */
function capabilityTone(ready: boolean, videoStatus: Video["status"]): Tone {
  if (ready) return "ai";
  if (videoStatus === "processing" || videoStatus === "uploaded") return "progress";
  return "neutral";
}

function capabilityLabel(ready: boolean, videoStatus: Video["status"]): string {
  if (ready) return "Ready";
  if (videoStatus === "processing" || videoStatus === "uploaded") return "Processing";
  return "Not available";
}

/**
 * "AI Video Brief" — an asymmetric editorial layout, not a stack of
 * dashboard cards: a large executive summary leads on the left, a
 * compact capability/insight stack sits to its right, and a chapter
 * timeline runs full-width beneath both. Every value here is real
 * (useMeeting's aggregate + useChapters/useFlashcards, all polling
 * per the same terminal-status logic as every other panel).
 */
export function OverviewPanel({ video, onNavigate }: OverviewPanelProps) {
  const meeting = useMeeting(video.id);
  const chapters = useChapters(video.id, video.status);
  const flashcards = useFlashcards(video.id, video.status);
  const player = useVideoPlayer();
  // Claims the shared Workspace accent slot only for the render passes
  // that actually mount the status-badge Workspace3DObject below (see
  // AccentSlotContext.tsx) - called unconditionally (rules of hooks),
  // with the same real availability check the accent's own render
  // guard depends on.
  useAccentSlotClaim(!meeting.isLoading && !meeting.isError);

  if (meeting.isLoading) {
    return (
      <div className="flex flex-col gap-4 p-6">
        <Skeleton className="h-8 w-2/3" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-24 w-full" />
      </div>
    );
  }

  if (meeting.isError) {
    return <ErrorState error={toApiError(meeting.error)} onRetry={() => meeting.refetch()} compact />;
  }

  const data = meeting.data!;
  const summary = data.summaries[0];
  const translation = data.translations[0];
  const quizCount = data.quizzes.length;
  const chapterList = chapters.data ?? [];
  const flashcardCount = flashcards.data?.length ?? 0;

  const capabilities: Capability[] = [
    { section: "transcript", icon: "transcript", label: "Transcript", ready: Boolean(data.transcript) },
    { section: "summary", icon: "summary", label: "Summary", ready: Boolean(summary) },
    { section: "translation", icon: "translate", label: "Translation", ready: Boolean(translation) },
    { section: "chapters", icon: "chapters", label: "Chapters", ready: chapterList.length > 0, count: chapterList.length },
    { section: "quiz", icon: "quiz", label: "Quiz", ready: quizCount > 0, count: quizCount },
    { section: "flashcards", icon: "flashcard", label: "Flashcards", ready: flashcardCount > 0, count: flashcardCount },
  ];
  const readyCount = capabilities.filter((capability) => capability.ready).length;

  // rs_status_badges.glb bakes all three states as nested groups in
  // one file (see registry.ts's STATUS_BADGE_GROUPS) - hiding the
  // other two leaves only the one matching this video's own real
  // `status`, so the accent visually confirms the same fact
  // `videoStatusLabel` already states in text, never a second/
  // duplicate signal.
  const statusBadgeHide = statusBadgeHideNodes(
    video.status === "processed" ? "ready" : video.status === "failed" ? "failed" : "processing",
  );

  return (
    <div className="flex flex-col gap-8 p-6 sm:p-8">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-label font-medium uppercase tracking-[0.14em] text-accent">AI Video Brief</p>
          <h1 className="mt-2 font-display text-display-lg font-semibold leading-tight text-text-primary">
            {video.title}
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-body-sm text-text-muted">
            <span>{formatDate(video.created_at)}</span>
            {video.duration > 0 && <span className="font-mono">{formatTimecode(video.duration)}</span>}
            {video.language !== "unknown" && <span className="uppercase tracking-wide">{video.language}</span>}
            <span>{videoStatusLabel(video.status)}</span>
          </div>
        </div>
        <Workspace3DObject
          model="statusBadges"
          hideNodes={statusBadgeHide}
          loopClip="Pulse"
          className="hidden h-14 w-20 shrink-0 sm:block"
        />
      </div>

      {/*
       * A single editorial column, not a side-by-side grid - the old
       * `lg:grid-cols-[1fr_300px]` split was tuned for the full-width
       * layout this panel used to run in. Now that the Workspace is a
       * real video|content split (see the workspace page), this column
       * is itself only ~400-570px wide even on a large desktop, which
       * is too narrow for a fixed 300px side panel to breathe next to
       * an editorial lead paragraph - found live, it left the summary
       * crushed into roughly 230-270px. Stacking reads better at every
       * one of these narrower widths, and still feels like a real
       * report (summary, then readiness, then chapters), not a
       * dashboard forcing itself into a column too narrow for it.
       */}
      <div className="flex flex-col gap-8">
        {/* Executive summary — large, editorial lead, not a truncated card. */}
        <section className="min-w-0">
          <p className="text-label font-semibold uppercase tracking-wide text-text-secondary">Executive summary</p>
          {summary ? (
            <p className="mt-3 text-heading-sm font-medium leading-relaxed text-text-primary">
              {truncate(summary.content, 480)}
            </p>
          ) : (
            <p className="mt-3 text-body leading-relaxed text-text-muted">
              {video.status === "processed"
                ? "This video finished processing without producing a summary."
                : "The summary is being generated — this will fill in automatically."}
            </p>
          )}
          {summary && (
            <button
              type="button"
              onClick={() => onNavigate("summary")}
              className="mt-3 text-body-sm font-medium text-accent transition-colors duration-fast hover:text-accent-hover"
            >
              Read the full brief →
            </button>
          )}

          {data.transcript && (
            <div className="mt-8 border-t border-border pt-6">
              <p className="text-label font-semibold uppercase tracking-wide text-text-secondary">From the transcript</p>
              <p className="mt-3 text-body-sm leading-relaxed text-text-secondary">{truncate(data.transcript.text, 260)}</p>
              <button
                type="button"
                onClick={() => onNavigate("transcript")}
                className="mt-3 text-body-sm font-medium text-accent transition-colors duration-fast hover:text-accent-hover"
              >
                Open transcript →
              </button>
            </div>
          )}
        </section>

        {/*
         * Readiness — a two-column strip of compact badges rather than
         * a stacked list, now that it has the full column width to
         * itself instead of a cramped 300px sidebar - reads as one
         * quick scan of "what's ready" instead of a tall list.
         */}
        <section className="min-w-0 border-t border-border pt-6">
          <div className="flex items-center justify-between">
            <p className="text-label font-semibold uppercase tracking-wide text-text-secondary">Readiness</p>
            <span className="font-mono text-caption text-text-muted">
              {readyCount}/{capabilities.length}
            </span>
          </div>
          <button
            type="button"
            onClick={() => onNavigate("chat")}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-ai px-4 py-2 text-body-sm font-medium text-ai-on transition-colors duration-fast hover:bg-ai-hover"
          >
            <Icon name="chat" size={14} />
            Ask about this video
          </button>
          <div className="mt-4 grid grid-cols-1 gap-x-4 gap-y-0.5 divide-y divide-border sm:grid-cols-2 sm:divide-y-0">
            {capabilities.map((capability) => (
              <button
                key={capability.section}
                type="button"
                onClick={() => onNavigate(capability.section)}
                className="group flex items-center justify-between gap-2 py-2.5 text-left transition-colors duration-fast"
              >
                <span className="flex min-w-0 items-center gap-2.5">
                  <Icon name={capability.icon} size={14} className="shrink-0 text-text-muted group-hover:text-accent" />
                  <span className="truncate text-body-sm text-text-secondary group-hover:text-text-primary">
                    {capability.label}
                    {typeof capability.count === "number" && capability.count > 0 && (
                      <span className="ml-1.5 font-mono text-caption text-text-muted">{capability.count}</span>
                    )}
                  </span>
                </span>
                <BaseBadge
                  tone={capabilityTone(capability.ready, video.status)}
                  label={capabilityLabel(capability.ready, video.status)}
                  pulse={!capability.ready && (video.status === "processing" || video.status === "uploaded")}
                />
              </button>
            ))}
          </div>
        </section>
      </div>

      {/* Chapter timeline — full width, bottom. */}
      {chapterList.length > 0 && (
        <section className="border-t border-border pt-6">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-label font-semibold uppercase tracking-wide text-text-secondary">Chapters</p>
            <button
              type="button"
              onClick={() => onNavigate("chapters")}
              className="text-caption font-medium text-accent transition-colors duration-fast hover:text-accent-hover"
            >
              Open narrative map →
            </button>
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {chapterList.map((chapter) => {
              const isActive = player.currentTime >= chapter.start_time && player.currentTime < chapter.end_time;
              return (
                <button
                  key={chapter.id}
                  type="button"
                  onClick={() => player.seek(chapter.start_time)}
                  className={cn(
                    "shrink-0 rounded-md border px-3 py-2 text-left transition-colors duration-fast",
                    isActive ? "border-accent-border bg-accent-muted" : "border-border hover:border-border-strong hover:bg-surface-hover",
                  )}
                >
                  <p className="font-mono text-caption text-text-muted">{formatTimecode(chapter.start_time)}</p>
                  <p className="mt-0.5 max-w-[16ch] truncate text-body-sm font-medium text-text-primary">{chapter.title}</p>
                </button>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
