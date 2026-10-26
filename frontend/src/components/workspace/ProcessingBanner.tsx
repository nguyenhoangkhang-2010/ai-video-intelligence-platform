"use client";

import { JobStatusBadge } from "@/components/ui/StatusBadge";
import { Icon } from "@/components/ui/Icon";
import { Button } from "@/components/ui/Button";
import { useRetryProcessingJob, useVideoProcessingJobs } from "@/hooks/useVideos";
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
  const retry = useRetryProcessingJob(video.id);

  if (video.status === "processed") return null;

  // A FAILED latest job counts as failed even if the video row itself
  // never left "uploaded" (dispatch never started) - otherwise that case
  // would fall through to a progress bar stuck forever.
  if (video.status === "failed" || job?.status === "FAILED") {
    const canRetry = job?.status === "FAILED";
    return (
      <div className="flex items-start gap-3 border-b border-error/40 border-l-4 border-l-error bg-error-muted px-4 py-3 sm:px-6">
        <Icon name="alert" size={17} className="mt-0.5 shrink-0 text-error" />
        <div className="min-w-0 flex-1">
          <p className="text-body-sm font-medium text-error">Processing failed</p>
          <p className="mt-0.5 break-words text-caption text-text-secondary">
            {jobsQuery.isError
              ? `Couldn't load the failure details: ${toApiError(jobsQuery.error).message}`
              : (job?.error_message ?? "The video couldn't be processed. Try uploading it again.")}
          </p>
          {retry.isError && (
            <p role="alert" className="mt-1 text-caption font-medium text-error">
              {toApiError(retry.error).message}
            </p>
          )}
        </div>
        {jobsQuery.isError && (
          <Button variant="secondary" size="sm" className="shrink-0" onClick={() => jobsQuery.refetch()}>
            <Icon name="refresh" size={13} />
            Reload status
          </Button>
        )}
        {canRetry && (
          <Button
            variant="secondary"
            size="sm"
            className="shrink-0"
            isLoading={retry.isPending}
            onClick={() => job && retry.mutate(job.id)}
          >
            {!retry.isPending && <Icon name="refresh" size={13} />}
            Retry processing
          </Button>
        )}
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
      <div className="flex items-start gap-3 border-b border-error/40 border-l-4 border-l-error bg-error-muted px-4 py-3 sm:px-6">
        <Icon name="alert" size={17} className="mt-0.5 shrink-0 text-error" />
        <div className="min-w-0 flex-1">
          <p className="text-body-sm font-medium text-error">Couldn&apos;t load processing status</p>
          <p className="mt-0.5 text-caption text-text-secondary">{toApiError(jobsQuery.error).message}</p>
        </div>
        <button
          type="button"
          onClick={() => jobsQuery.refetch()}
          aria-label="Retry"
          className="flex shrink-0 items-center gap-1.5 border border-error/60 bg-surface-elevated px-2 py-1 text-caption font-medium text-error transition-colors duration-fast hover:bg-error-muted"
        >
          <Icon name="refresh" size={12} />
          Retry
        </button>
      </div>
    );
  }

  const progress = job?.progress ?? 0;

  return (
    <div className="flex items-center gap-4 border-b border-text-primary/25 bg-surface px-4 py-2.5 sm:px-6">
      <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-[3px] border-ai bg-surface-sunken" aria-hidden="true">
        <span className="absolute inset-0 animate-spin" style={{ animationDuration: "2.4s" }}>
          <span className="absolute left-1/2 top-[3px] h-[11px] w-[2px] -translate-x-1/2 bg-ai" />
        </span>
        <span className="h-1.5 w-1.5 rounded-full bg-text-primary" />
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-baseline justify-between gap-2">
          <p className="truncate text-body-sm font-medium text-text-primary">
            {job?.current_step ?? "Processing video…"}
          </p>
          <span className="shrink-0 font-mono text-caption text-ai">{progress}%</span>
        </div>
        <div className="mt-1.5 h-[5px] w-full border border-text-primary/40 bg-surface-elevated">
          <div className="h-full bg-ai transition-[width] duration-base ease-calm" style={{ width: `${progress}%` }} />
        </div>
      </div>
      {job && <JobStatusBadge status={job.status} className="hidden sm:inline-flex" />}
    </div>
  );
}
