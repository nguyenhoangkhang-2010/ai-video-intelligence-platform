"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Nova } from "@/components/3d/Nova";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { PipelineTracker } from "@/components/upload/PipelineTracker";
import { useUpload } from "@/hooks/useUpload";
import { ROUTES } from "@/lib/constants";
import { cn, formatBytes } from "@/lib/utils";

const ACCEPTED_TYPES = ["video/mp4", "video/quicktime", "video/webm", "video/x-matroska"];

/**
 * Upload Studio — a real page (matches the ROUTES.upload constant
 * that already existed but had no page behind it), not a modal
 * dialog. Select → real byte-progress upload → the same real,
 * already-polling processing-job data the workspace's own
 * ProcessingBanner uses (see PipelineTracker.tsx) → an automatic
 * transition into the workspace once the video's real status becomes
 * "processed". No stage here is simulated.
 */
export default function UploadStudioPage() {
  const { stage, progress, fileName, error, video, upload, cancel, reset } = useUpload();
  const { notice } = useNovaAttention();
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (stage === "uploading") notice("attention");
    else if (stage === "error") notice("idle");
  }, [stage, notice]);

  function handleFile(file: File) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setValidationError(`"${file.name}" isn't a supported video format. Use MP4, MOV, WebM, or MKV.`);
      return;
    }
    setValidationError(null);
    setSelectedFile(file);
    void upload(file);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    const file = event.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <div className="atmosphere-glow pointer-events-none absolute -top-40 right-0 z-0 h-[560px] w-[560px]" aria-hidden="true" />

      <header className="relative z-10 flex shrink-0 items-center gap-3 border-b border-border px-4 py-2.5 sm:px-5">
        <Link
          href={ROUTES.library}
          aria-label="Back to library"
          className="flex h-8 w-8 shrink-0 items-center justify-center rounded text-text-muted transition-colors duration-fast hover:bg-surface-hover hover:text-text-primary"
        >
          <Icon name="arrow-left" size={17} />
        </Link>
        <div>
          <p className="text-label font-medium uppercase tracking-wide text-text-muted">Upload Studio</p>
        </div>
      </header>

      <div className="relative z-10 flex flex-1 flex-col items-center justify-center gap-8 overflow-y-auto p-6">
        <Nova state="idle" className="h-24 w-24 opacity-90 sm:h-32 sm:w-32" />

        {stage === "idle" && (
          <div className="w-full max-w-lg">
            <div
              onDragOver={(event) => {
                event.preventDefault();
                setIsDragging(true);
              }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
              }}
              className={cn(
                "flex cursor-pointer flex-col items-center gap-3 rounded-2xl border-2 border-dashed px-6 py-16 text-center transition-colors duration-base",
                isDragging ? "border-accent bg-accent-muted" : "border-border-strong hover:border-text-muted",
              )}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-elevated text-accent">
                <Icon name="upload" size={22} />
              </div>
              <div>
                <p className="text-body font-medium text-text-primary">Drop a video here, or click to browse</p>
                <p className="mt-1 text-caption text-text-muted">MP4, MOV, WebM, or MKV — processing starts automatically.</p>
              </div>
              <input
                ref={inputRef}
                type="file"
                accept={ACCEPTED_TYPES.join(",")}
                className="sr-only"
                onChange={(event) => {
                  const file = event.target.files?.[0];
                  if (file) handleFile(file);
                }}
              />
            </div>

            {validationError && (
              <p role="alert" className="mt-3 flex items-start gap-1.5 rounded border border-error/30 bg-error-muted px-3 py-2 text-caption text-error">
                <Icon name="alert" size={14} className="mt-0.5 shrink-0" />
                {validationError}
              </p>
            )}
          </div>
        )}

        {stage === "uploading" && (
          <div className="w-full max-w-md">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded bg-ai-muted text-ai">
                <Icon name="video" size={18} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-body-sm font-medium text-text-primary">{fileName}</p>
                <p className="text-caption text-text-muted">
                  Uploading — {progress}%{selectedFile && ` · ${formatBytes(selectedFile.size)}`}
                </p>
              </div>
            </div>
            <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-surface-elevated">
              <div className="h-full rounded-full bg-ai transition-[width] duration-base ease-calm" style={{ width: `${progress}%` }} />
            </div>
            <Button variant="secondary" size="sm" className="mt-4" onClick={cancel}>
              Cancel upload
            </Button>
          </div>
        )}

        {(stage === "processing" || (stage === "success" && video)) && video && <PipelineTracker videoId={video.id} />}

        {stage === "error" && (
          <div className="flex flex-col items-center gap-3 text-center">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-error-muted text-error">
              <Icon name="alert" size={20} />
            </div>
            <div>
              <p className="text-body font-medium text-text-primary">Upload failed</p>
              <p className="mt-1 max-w-sm text-body-sm text-text-muted">{error}</p>
            </div>
            <Button
              size="sm"
              onClick={() => {
                reset();
                setSelectedFile(null);
              }}
            >
              Try again
            </Button>
          </div>
        )}

        {stage === "idle" && (
          <p className="max-w-sm text-center text-caption text-text-disabled">
            Ingest → Transcribe → Understand → Index → Ready — the same real pipeline every video goes through.
          </p>
        )}
      </div>
    </div>
  );
}
