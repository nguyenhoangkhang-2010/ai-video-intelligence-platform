"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { useDeleteVideo } from "@/hooks/useVideos";
import { ROUTES } from "@/lib/constants";
import { formatDate, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

export function WorkspaceHeader({ video }: { video: Video }) {
  const router = useRouter();
  const deleteVideo = useDeleteVideo();
  const [confirmDelete, setConfirmDelete] = useState(false);

  return (
    <header className="flex shrink-0 items-start justify-between gap-4 border-b border-border px-5 py-5 sm:px-8 sm:py-6">
      <div className="flex min-w-0 items-start gap-3">
        <Link
          href={ROUTES.library}
          aria-label="Back to library"
          className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded text-text-muted transition-colors duration-fast hover:bg-surface-hover hover:text-text-primary"
        >
          <Icon name="arrow-left" size={17} />
        </Link>
        <div className="min-w-0">
          <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-caption uppercase tracking-wider text-text-disabled">
            <Link href={ROUTES.library} className="transition-colors duration-fast hover:text-text-secondary">
              Library
            </Link>
            <Icon name="chevron-right" size={10} aria-hidden="true" />
            <span>Workspace</span>
          </nav>
          <h1
            className="mt-1 truncate font-display text-heading font-semibold leading-tight tracking-tight text-text-primary"
            title={video.title}
          >
            {video.title}
          </h1>
          <p className="mt-1.5 truncate text-body-sm text-text-muted">
            {formatDate(video.created_at)}
            {video.duration > 0 && ` · ${formatTimecode(video.duration)}`}
            {video.language !== "unknown" && ` · ${video.language.toUpperCase()}`}
          </p>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-3">
        <VideoStatusBadge status={video.status} />
        <button
          type="button"
          onClick={() => setConfirmDelete(true)}
          aria-label="Delete video"
          className="flex h-8 w-8 items-center justify-center rounded text-text-muted hover:bg-error-muted hover:text-error"
        >
          <Icon name="trash" size={16} />
        </button>
      </div>

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this video?"
        description={`"${video.title}" and everything generated from it will be permanently removed.`}
        confirmLabel="Delete video"
        danger
        isConfirming={deleteVideo.isPending}
        onCancel={() => setConfirmDelete(false)}
        onConfirm={() => {
          deleteVideo.mutate(video.id, {
            onSuccess: () => router.push(ROUTES.library),
          });
        }}
      />
    </header>
  );
}
