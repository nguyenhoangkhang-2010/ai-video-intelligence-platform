"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { useDeleteVideo } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import { ROUTES } from "@/lib/constants";
import { formatDate, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

export function WorkspaceHeader({ video }: { video: Video }) {
  const router = useRouter();
  const deleteVideo = useDeleteVideo();
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <header className="flex shrink-0 items-center justify-between gap-4 border-b-2 border-text-primary px-4 py-2 sm:px-6">
      <div className="flex min-w-0 items-center gap-3.5">
        <Link
          href={ROUTES.library}
          aria-label="Back to library"
          className="flex h-9 w-9 shrink-0 items-center justify-center border border-text-primary/50 text-text-primary transition-colors duration-fast hover:bg-surface"
        >
          <Icon name="arrow-left" size={17} />
        </Link>
        <div className="min-w-0">
          <nav aria-label="Breadcrumb" className="index-label flex items-center gap-1.5 text-text-muted">
            <Link href={ROUTES.library} className="transition-colors duration-fast hover:text-text-primary">
              Library
            </Link>
            <span aria-hidden="true">/</span>
            <span>Calibre {String(video.id).padStart(3, "0")}</span>
            {/*
             * Date/duration/language ride on the breadcrumb line (one
             * quiet fact, one row) so the header stays two lines tall and
             * the dial below gets the height. Status is deliberately not
             * repeated here - VideoStatusBadge at the right already says it.
             */}
            <span className="hidden truncate normal-case tracking-normal text-text-secondary sm:inline">
              · {formatDate(video.created_at)}
              {video.duration > 0 && ` · ${formatTimecode(video.duration)}`}
              {video.language !== "unknown" && ` · ${video.language.toUpperCase()}`}
            </span>
          </nav>
          <h1
            className="truncate font-display text-heading-sm font-semibold leading-tight tracking-tight text-text-primary"
            title={video.title}
          >
            {video.title}
          </h1>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <VideoStatusBadge status={video.status} />
        <button
          type="button"
          onClick={() => setConfirmDelete(true)}
          aria-label="Delete video"
          className="flex h-9 w-9 items-center justify-center border border-transparent text-text-secondary transition-colors duration-fast hover:border-error/60 hover:bg-error-muted hover:text-error"
        >
          <Icon name="trash" size={16} />
        </button>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this video?"
        description={`"${video.title}" and everything generated from it will be permanently removed.`}
        error={deleteVideo.isError ? toApiError(deleteVideo.error).message : null}
        confirmLabel={deleteVideo.isError ? "Try again" : "Delete video"}
        danger
        isConfirming={deleteVideo.isPending}
        onCancel={() => {
          setConfirmDelete(false);
          deleteVideo.reset();
        }}
        onConfirm={() => {
          // Only navigates away on success - a failed delete keeps the
          // dialog open with the real error shown above (previously
          // there was no onError/isError handling at all here, so a
          // failure was silently invisible).
          deleteVideo.mutate(video.id, {
            onSuccess: () => router.push(ROUTES.library),
          });
        }}
      />
    </header>
  );
}
