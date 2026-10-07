"use client";

import { JobStatusBadge } from "@/components/ui/StatusBadge";
import { Icon } from "@/components/ui/Icon";
import { useAccentSlotClaim } from "@/components/3d/workspace3d/AccentSlotContext";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { PIPELINE_STEP_TO_STAGE } from "@/components/3d/workspace3d/registry";
import { useVideoProcessingJobs } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import type { Video } from "@/types/video";

/**
 * Surfaces real ProcessingJob progress/current_step (see
 * app/pipelines/video_pipeline.py — every step name and percentage
 * rendered here, e.g. "Transcribing" at 70%, is a literal value the
 * pipeline reports, never invented client-side). Hidden once the
 * video is processed; the failure case shows the job's own
 * error_message rather than a generic message.
 */
export function ProcessingBanner({ video }: { video: Video }) {
  const jobsQuery = useVideoProcessingJobs(video.id, video.status !== "processed");
  const jobs = jobsQuery.data;
  const job = jobs?.[jobs.length - 1];
  // Claims the shared Workspace accent slot only for the pipeline
  // scrub accent's own real render condition (see
  // AccentSlotContext.tsx) - the "failed"/error branches below show no
  // Workspace3DObject, so they don't claim.
  useAccentSlotClaim(video.status !== "processed" && video.status !== "failed" && !jobsQuery.isError);

  if (video.status === "processed") return null;

  if (video.status === "failed") {
    return (
      <div className="flex items-start gap-3 border-b border-error/25 bg-error-muted px-4 py-3 sm:px-5">
        <Icon name="alert" size={17} className="mt-0.5 shrink-0 text-error" />
        <div className="min-w-0 flex-1">
          <p className="text-body-sm font-medium text-error">Processing failed</p>
          <p className="mt-0.5 text-caption text-text-secondary">
            {job?.error_message ?? "The video couldn't be processed. Try uploading it again."}
          </p>
        </div>
      </div>
    );
  }

  // A genuine fetch failure here must never look like silent, stalled
  // progress (the same job/undefined -> "Processing video… 0%" every
  // other branch below would otherwise render forever) - this is the
  // one signal telling the person something actually went wrong, not
  // that the pipeline is just slow.
  if (jobsQuery.isError) {
    return (
      <div className="flex items-start gap-3 border-b border-error/25 bg-error-muted px-4 py-3 sm:px-5">
        <Icon name="alert" size={17} className="mt-0.5 shrink-0 text-error" />
        <div className="min-w-0 flex-1">
          <p className="text-body-sm font-medium text-error">Couldn&apos;t load processing status</p>
          <p className="mt-0.5 text-caption text-text-secondary">{toApiError(jobsQuery.error).message}</p>
        </div>
        <button
          type="button"
          onClick={() => jobsQuery.refetch()}
          aria-label="Retry"
          className="flex shrink-0 items-center gap-1.5 rounded border border-error/30 px-2 py-1 text-caption font-medium text-error transition-colors duration-fast hover:bg-error-muted"
        >
          <Icon name="refresh" size={12} />
          Retry
        </button>
      </div>
    );
  }

  const progress = job?.progress ?? 0;
  // Real backend step -> the pipeline model's 5 coarser visual stages
  // (see registry.ts for the full step list and why a step not in the
  // map still degrades safely to stage 0 rather than crashing).
  const stageIndex = job?.current_step ? (PIPELINE_STEP_TO_STAGE[job.current_step] ?? 0) : 0;

  return (
    <div className="flex items-center gap-4 border-b border-ai-border bg-ai-muted px-4 py-3 sm:px-5">
      {/*
       * rs_pipeline.glb (ui-3d/README.md), scrubbed - not played on its
       * own clock - directly from this real stage index / 4, so the 5
       * lit segments always reflect the actual backend ProcessingJob
       * state, never an invented animation timer. Falls back to the
       * plain pulsing clock glyph below hydration/Suspense.
       */}
      <Workspace3DObject
        model="pipeline"
        scrubClip="Process"
        scrubProgress={stageIndex / 4}
        className="h-14 w-24 shrink-0 sm:h-16 sm:w-28"
      />
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className="truncate text-body-sm font-medium text-text-primary">
            {job?.current_step ?? "Processing video…"}
          </p>
          <span className="shrink-0 font-mono text-caption text-ai">{progress}%</span>
        </div>
        <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-surface-elevated">
          <div
            className="h-full rounded-full bg-ai transition-[width] duration-base ease-calm"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
      {job && <JobStatusBadge status={job.status} className="hidden sm:inline-flex" />}
    </div>
  );
}
