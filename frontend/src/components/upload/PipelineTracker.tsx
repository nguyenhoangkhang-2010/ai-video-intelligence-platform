"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Icon } from "@/components/ui/Icon";
import { useVideo, useVideoProcessingJobs } from "@/hooks/useVideos";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

const STAGES = ["Ingest", "Transcribe", "Understand", "Index", "Ready"] as const;

/**
 * Groups the pipeline's own real `current_step` values (see
 * app/pipelines/video_pipeline.py - "Extract Metadata", "Transcribing",
 * "Generating Summary", "Generating Embeddings", "Completed", etc.,
 * confirmed by reading that file directly) into the five stages above.
 * Never invents progress a step name doesn't report - an unrecognized
 * future step name falls back to whichever stage its real % progress
 * places it nearest, not a guess at its meaning.
 */
function stageIndexFor(currentStep: string | null | undefined, progress: number): number {
  if (!currentStep) return 0;
  const step = currentStep.toLowerCase();
  if (step === "completed") return 4;
  if (step.includes("transcri")) return 1;
  if (step.includes("summary") || step.includes("translation") || step.includes("quiz") || step.includes("chapter")) return 2;
  if (step.includes("embedding") || step.includes("index")) return 3;
  if (step.includes("metadata")) return 0;
  // Unrecognized step name - place it by real progress rather than guessing its meaning.
  if (progress >= 100) return 4;
  if (progress >= 96) return 3;
  if (progress >= 91) return 2;
  if (progress >= 30) return 1;
  return 0;
}

/**
 * Live pipeline visualization for a just-uploaded video, backed by
 * the same real, already-polling hooks the workspace's own
 * ProcessingBanner uses (useVideo, useVideoProcessingJobs) - not a
 * separate fake progress simulation. Auto-navigates to the workspace
 * the moment the video's real status actually becomes "processed".
 */
export function PipelineTracker({ videoId }: { videoId: number }) {
  const router = useRouter();
  const video = useVideo(videoId);
  const { data: jobs } = useVideoProcessingJobs(videoId, true);
  const { notice } = useNovaAttention();
  const job = jobs?.[jobs.length - 1];
  const progress = job?.progress ?? 0;
  const isFailed = video.data?.status === "failed";
  const isReady = video.data?.status === "processed";
  const activeIndex = isReady ? 4 : stageIndexFor(job?.current_step, progress);

  useEffect(() => {
    if (isReady) notice("excited", 1400);
    else if (isFailed) notice("idle");
    else notice("thinking");
  }, [isReady, isFailed, notice]);

  useEffect(() => {
    if (!isReady) return;
    const timeout = setTimeout(() => router.push(ROUTES.video(videoId)), 1100);
    return () => clearTimeout(timeout);
  }, [isReady, router, videoId]);

  if (isFailed) {
    return (
      <div className="flex flex-col items-center gap-3 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-error-muted text-error">
          <Icon name="alert" size={22} />
        </span>
        <div>
          <p className="text-body font-medium text-text-primary">Processing failed</p>
          <p className="mt-1 max-w-sm text-body-sm text-text-muted">
            {job?.error_message ?? "The pipeline couldn't finish processing this video."}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-lg flex-col items-center gap-6 text-center">
      <div className="flex w-full items-center">
        {STAGES.map((stage, index) => (
          <div key={stage} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-2">
              <span
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border font-mono text-caption transition-colors duration-spatial",
                  index < activeIndex
                    ? "border-ai bg-ai text-ai-on"
                    : index === activeIndex
                      ? "border-ai bg-ai-muted text-ai"
                      : "border-border-strong bg-surface text-text-muted",
                )}
              >
                {index < activeIndex ? <Icon name="check" size={14} /> : index + 1}
              </span>
              <span
                className={cn(
                  "text-caption font-medium",
                  index <= activeIndex ? "text-text-primary" : "text-text-muted",
                )}
              >
                {stage}
              </span>
            </div>
            {index < STAGES.length - 1 && (
              <div className="mx-2 h-px flex-1 bg-border-strong">
                <div
                  className="h-full bg-ai transition-[width] duration-spatial ease-spatial"
                  style={{ width: index < activeIndex ? "100%" : "0%" }}
                />
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="w-full">
        <p className="text-body-sm font-medium text-text-primary">
          {isReady ? "Ready — opening your workspace…" : job?.current_step ?? "Starting…"}
        </p>
        <div className="mt-2 h-1 w-full overflow-hidden rounded-full bg-surface-elevated">
          <div
            className="h-full rounded-full bg-ai transition-[width] duration-base ease-calm"
            style={{ width: `${isReady ? 100 : progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}
