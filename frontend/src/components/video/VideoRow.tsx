"use client";

import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { VideoActionsMenu } from "@/components/video/VideoActionsMenu";
import { VideoThumbnail } from "@/components/video/VideoThumbnail";
import { ROUTES } from "@/lib/constants";
import { formatDate, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

interface VideoRowProps {
  video: Video;
  index: number;
  onDelete: (video: Video) => void;
}

/**
 * The library's list view - a compact register for scanning many
 * videos at once (the dial view is for browsing). Real extracted frame
 * when one exists (see VideoThumbnail), otherwise the honest abstract
 * surface.
 */
export function VideoRow({ video, index, onDelete }: VideoRowProps) {
  return (
    <div className="group relative grid grid-cols-[auto_auto_minmax(0,1fr)_auto] items-center gap-4 border-b border-text-primary/20 py-3 transition-colors duration-fast hover:bg-surface sm:grid-cols-[3rem_auto_minmax(0,1fr)_auto_auto_auto] sm:gap-5 sm:px-2">
      <span className="hidden font-mono text-caption text-text-muted sm:block">{String(index).padStart(3, "0")}</span>

      <Link
        href={ROUTES.video(video.id)}
        aria-label={video.title}
        className="relative aspect-video w-24 shrink-0 overflow-hidden border border-text-primary/30 bg-surface-sunken sm:w-32"
      >
        <VideoThumbnail video={video} patternSpacing={14} />
        <span className="absolute inset-0 flex items-center justify-center">
          <Icon
            name="play"
            size={16}
            className="rounded-full bg-surface-elevated p-1.5 text-text-primary opacity-0 transition-opacity duration-base group-hover:opacity-100"
          />
        </span>
      </Link>

      <Link href={ROUTES.video(video.id)} className="min-w-0">
        <h3 className="truncate font-display text-body-sm font-semibold text-text-primary transition-colors duration-fast group-hover:text-accent">
          {video.title}
        </h3>
        <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-caption text-text-secondary">
          <span>{formatDate(video.created_at)}</span>
          {video.language !== "unknown" && (
            <>
              <span aria-hidden="true">·</span>
              <span className="uppercase tracking-wide">{video.language}</span>
            </>
          )}
        </p>
      </Link>

      <span className="hidden font-mono text-caption text-text-secondary sm:block">
        {video.duration > 0 ? formatTimecode(video.duration) : "--:--"}
      </span>

      <div className="hidden shrink-0 sm:block">
        <VideoStatusBadge status={video.status} />
      </div>

      <VideoActionsMenu video={video} onDelete={onDelete} />
    </div>
  );
}
