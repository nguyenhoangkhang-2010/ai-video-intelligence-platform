"use client";

import Link from "next/link";
import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { ROUTES } from "@/lib/constants";
import { cn, formatDate, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

interface VideoRowProps {
  video: Video;
  onDelete: (video: Video) => void;
}

/**
 * A horizontal media-archive row, not a grid card — the library reads
 * as a list of media objects with real metadata, not a wall of
 * identical tiles. Same honesty constraint as the old VideoCard it
 * replaces: no thumbnail exists in the API, so the slate stays an
 * abstract media surface, never a faked frame.
 */
export function VideoRow({ video, onDelete }: VideoRowProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const isProcessing = video.status === "uploaded" || video.status === "processing";

  return (
    <div className="group relative flex items-center gap-4 py-3 transition-colors duration-fast hover:bg-surface-hover sm:gap-5 sm:px-3">
      <Link
        href={ROUTES.video(video.id)}
        aria-label={video.title}
        className="relative aspect-video w-28 shrink-0 overflow-hidden rounded-md bg-[radial-gradient(ellipse_at_top_left,rgb(var(--color-surface-elevated))_0%,rgb(var(--color-surface-sunken))_72%)] sm:w-36"
      >
        <div
          className="absolute inset-0 opacity-[0.06] transition-opacity duration-base group-hover:opacity-[0.12]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(115deg, rgb(var(--color-ai)) 0px, rgb(var(--color-ai)) 1px, transparent 1px, transparent 18px)",
          }}
          aria-hidden="true"
        />
        <span className="absolute inset-0 flex items-center justify-center">
          <Icon
            name="play"
            size={16}
            className="text-text-disabled opacity-70 transition-[opacity,transform] duration-base ease-calm group-hover:scale-110 group-hover:text-accent group-hover:opacity-100"
          />
        </span>
        {video.duration > 0 && (
          <span className="absolute bottom-1 right-1 rounded bg-bg/80 px-1 py-0.5 font-mono text-[10px] text-text-secondary backdrop-blur-[2px]">
            {formatTimecode(video.duration)}
          </span>
        )}
        {isProcessing && (
          <div className="absolute inset-x-0 top-0 h-0.5 overflow-hidden bg-transparent">
            <div className="h-full w-1/3 animate-[shimmer_1.8s_ease-in-out_infinite] bg-ai" />
          </div>
        )}
      </Link>

      <Link href={ROUTES.video(video.id)} className="min-w-0 flex-1">
        <h3 className="truncate text-body-sm font-medium text-text-primary transition-colors duration-fast group-hover:text-accent">
          {video.title}
        </h3>
        <p className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-caption text-text-muted">
          <span>{formatDate(video.created_at)}</span>
          {video.language !== "unknown" && (
            <>
              <span aria-hidden="true">·</span>
              <span className="uppercase tracking-wide">{video.language}</span>
            </>
          )}
        </p>
      </Link>

      <div className="hidden shrink-0 sm:block">
        <VideoStatusBadge status={video.status} />
      </div>

      <div className="relative shrink-0">
        <button
          type="button"
          aria-label="Video actions"
          aria-haspopup="menu"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((value) => !value)}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded text-text-muted opacity-0 transition-opacity duration-fast hover:bg-surface-elevated hover:text-text-primary focus-visible:opacity-100 group-hover:opacity-100",
            menuOpen && "opacity-100",
          )}
        >
          <Icon name="more" size={16} />
        </button>
        {menuOpen && (
          <>
            <div className="fixed inset-0 z-dropdown" onClick={() => setMenuOpen(false)} />
            <div role="menu" aria-label="Video actions" className="absolute right-0 top-8 z-dropdown w-36 rounded border border-border-strong bg-surface-elevated py-1 shadow-md">
              <button
                type="button"
                role="menuitem"
                onClick={() => {
                  setMenuOpen(false);
                  onDelete(video);
                }}
                className="flex w-full items-center gap-2 px-3 py-1.5 text-left text-body-sm text-error hover:bg-surface-hover"
              >
                <Icon name="trash" size={14} />
                Delete
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
