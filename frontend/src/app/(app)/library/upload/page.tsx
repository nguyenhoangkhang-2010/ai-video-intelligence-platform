"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type DragEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Nova } from "@/components/3d/Nova";
import { DialRing } from "@/components/dial/DialRing";
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
    <div className="flex h-full flex-col overflow-hidden">
      <header className="flex shrink-0 items-center gap-4 border-b border-text-primary/25 px-4 py-3 sm:px-8">
        <Link
          href={ROUTES.library}
          aria-label="Back to library"
          className="flex h-9 w-9 shrink-0 items-center justify-center border border-text-primary/50 text-text-primary transition-colors duration-fast hover:bg-surface"
        >
          <Icon name="arrow-left" size={17} />
        </Link>
        <div className="min-w-0 flex-1">
          <p className="index-label text-text-secondary">Upload studio · assembly bench</p>
          <p className="font-display text-heading font-semibold text-text-primary">Set a new movement</p>
        </div>
        <div className="relative h-12 w-12 shrink-0 rounded-full border-[3px] border-case bg-surface-sunken">
          <Nova state="idle" className="h-full w-full" />
        </div>
      </header>

      <div className="flex flex-1 flex-col items-center justify-center gap-8 overflow-y-auto p-6">
        {stage === "idle" && (
          <div className="flex w-full max-w-lg flex-col items-center">
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
              aria-label="Choose a video to upload"
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") inputRef.current?.click();
              }}
              className="group aspect-square w-full max-w-[360px] cursor-pointer rounded-full"
            >
              <DialRing ticks={60} caseWidth={4} emphasized={isDragging} progress={isDragging ? 1 : null} tone="lume">
                <div className="flex flex-col items-center gap-3 px-10 text-center">
                  <span
                    className={cn(
                      "flex h-16 w-16 items-center justify-center rounded-full border-2 transition-colors duration-base",
                      isDragging
                        ? "border-text-primary bg-lume text-lume-on"
                        : "border-text-primary/60 bg-surface-elevated text-text-primary group-hover:bg-lume group-hover:text-lume-on",
                    )}
                  >
                    <Icon name="upload" size={24} />
                  </span>
                  <p className="font-display text-body-lg font-semibold text-text-primary">
                    {isDragging ? "Release to set it in" : "Drop a video here"}
                  </p>
                  <p className="index-label text-text-secondary">or click to browse</p>
                </div>
              </DialRing>
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

            <p className="mt-6 text-center text-caption text-text-secondary">
              MP4, MOV, WebM or MKV — processing starts automatically.
            </p>

            {validationError && (
              <p role="alert" className="mt-4 flex w-full items-start gap-1.5 border-l-2 border-error bg-error-muted px-3 py-2 text-caption text-error">
                <Icon name="alert" size={14} className="mt-0.5 shrink-0" />
                {validationError}
              </p>
            )}
          </div>
        )}

        {stage === "uploading" && (
          <div className="flex w-full max-w-md flex-col items-center text-center">
            <div className="aspect-square w-full max-w-[260px]">
              <DialRing ticks={60} caseWidth={4} progress={progress / 100} tone="lume">
                <div className="flex flex-col items-center">
                  <span className="font-mono text-display font-medium text-text-primary">{progress}%</span>
                  <span className="index-label mt-1 text-text-secondary">Uploading</span>
                </div>
              </DialRing>
            </div>
            <p className="mt-6 max-w-full truncate font-display text-body font-semibold text-text-primary">{fileName}</p>
            {selectedFile && <p className="font-mono text-caption text-text-secondary">{formatBytes(selectedFile.size)}</p>}
            <Button variant="secondary" size="sm" className="mt-5" onClick={cancel}>
              Cancel upload
            </Button>
          </div>
        )}

        {(stage === "processing" || (stage === "success" && video)) && video && <PipelineTracker videoId={video.id} />}

        {stage === "error" && (
          <div className="flex flex-col items-center gap-3 text-center">
            <span className="flex h-12 w-12 items-center justify-center rounded-full border-[3px] border-error bg-error-muted text-error">
              <Icon name="alert" size={20} />
            </span>
            <div>
              <p className="font-display text-body-lg font-semibold text-text-primary">Upload failed</p>
              <p className="mt-1 max-w-sm text-body-sm text-text-secondary">{error}</p>
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
          <p className="index-label max-w-md text-center leading-relaxed text-text-muted">
            Ingest → Transcribe → Understand → Index → Ready
          </p>
        )}
      </div>
    </div>
  );
}
