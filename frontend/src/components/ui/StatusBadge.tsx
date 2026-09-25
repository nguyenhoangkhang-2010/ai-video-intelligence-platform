import { cn } from "@/lib/utils";
import { jobStatusLabel, videoStatusLabel } from "@/lib/utils";
import type { ProcessingJobStatus } from "@/types/processing";
import type { VideoStatus } from "@/types/video";

// "ai" is deliberately separate from "success" - it marks AI-GENERATED
// content readiness specifically (Overview's capability grid, RAG/
// search evidence) so it can use the cyan AI accent, never the
// generic pipeline-status green. Video/job lifecycle status keeps
// using "success" below - that's a pipeline state, not AI content.
//
// "progress" also uses the AI accent (not amber/warning) - "actively
// processing" IS active AI work, not a caution state, so it shares
// Nova's own color rather than competing with genuine warnings.
export type Tone = "neutral" | "info" | "progress" | "success" | "error" | "ai";

const toneClasses: Record<Tone, string> = {
  neutral: "bg-surface-elevated text-text-secondary border-border-strong",
  info: "bg-info-muted text-info border-info/30",
  progress: "bg-ai-muted text-ai border-ai-border",
  success: "bg-success-muted text-success border-success/30",
  error: "bg-error-muted text-error border-error/30",
  ai: "bg-ai-muted text-ai border-ai-border",
};

const videoStatusTone: Record<VideoStatus, Tone> = {
  uploaded: "info",
  processing: "progress",
  processed: "success",
  failed: "error",
};

const jobStatusTone: Record<ProcessingJobStatus, Tone> = {
  PENDING: "neutral",
  RUNNING: "progress",
  COMPLETED: "success",
  FAILED: "error",
};

interface StatusBadgeProps {
  className?: string;
}

/**
 * Status indicator that never relies on color alone — a matching
 * label/icon is always shown. Exported for any other place a
 * tone-coded status chip is needed (e.g. the Overview panel's
 * per-capability status grid) so every status chip in the app shares
 * one visual language instead of each screen inventing its own.
 */
export function BaseBadge({
  tone,
  label,
  pulse,
  className,
}: {
  tone: Tone;
  label: string;
  pulse?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-caption font-medium",
        toneClasses[tone],
        className,
      )}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full",
          tone === "neutral" && "bg-text-muted",
          tone === "info" && "bg-info",
          tone === "progress" && "bg-ai",
          tone === "success" && "bg-success",
          tone === "error" && "bg-error",
          tone === "ai" && "bg-ai",
          pulse && "animate-pulse",
        )}
        aria-hidden="true"
      />
      {label}
    </span>
  );
}

export function VideoStatusBadge({ status, className }: StatusBadgeProps & { status: VideoStatus }) {
  return (
    <BaseBadge
      tone={videoStatusTone[status]}
      label={videoStatusLabel(status)}
      pulse={status === "processing"}
      className={className}
    />
  );
}

export function JobStatusBadge({
  status,
  className,
}: StatusBadgeProps & { status: ProcessingJobStatus }) {
  return (
    <BaseBadge
      tone={jobStatusTone[status]}
      label={jobStatusLabel(status)}
      pulse={status === "RUNNING"}
      className={className}
    />
  );
}
