"use client";

import Link from "next/link";

import { DialRing, type DialTone } from "@/components/dial/DialRing";
import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { VideoActionsMenu } from "@/components/video/VideoActionsMenu";
import { VideoThumbnail } from "@/components/video/VideoThumbnail";
import { ROUTES } from "@/lib/constants";
import { cn, formatDate, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

/** Ring colour per lifecycle state - the "power reserve" indicator's hand colour. */
export function dialToneFor(video: Video): DialTone {
  if (video.status === "failed") return "error";
  if (video.status === "processed") return "lume";
  return "ai";
}

interface VideoDialProps {
  video: Video;
  /** 0..1 - this video's duration relative to the longest in view (the reserve arc). */
  reserve: number;
  index: number;
  onDelete: (video: Video) => void;
}

/**
 * One "watch" in the library's winder case: the real extracted frame
 * set into a round face, a reserve arc showing how long it runs
 * relative to the rest of the library, and the status in a date
 * window underneath.
 */
export function VideoDial({ video, reserve, index, onDelete }: VideoDialProps) {
  return (
    <article className="group relative flex flex-col items-center">
      <VideoActionsMenu video={video} onDelete={onDelete} className="absolute right-0 top-0 z-10" />

      <Link href={ROUTES.video(video.id)} aria-label={video.title} className="block aspect-square w-full max-w-[220px]">
        <DialRing
          progress={reserve}
          tone={dialToneFor(video)}
          ticks={60}
          caseWidth={5}
          className="transition-transform duration-base ease-calm group-hover:-rotate-6"
        >
          <span className="absolute inset-[17%] overflow-hidden rounded-full bg-surface">
            <VideoThumbnail video={video} patternSpacing={14} />
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface-elevated text-text-primary opacity-0 transition-opacity duration-base group-hover:opacity-100">
                <Icon name="play" size={18} />
              </span>
            </span>
          </span>
        </DialRing>
      </Link>

      <div className="mt-4 w-full max-w-[240px] text-center">
        <p className="index-label text-text-muted">No. {String(index).padStart(3, "0")}</p>
        <Link href={ROUTES.video(video.id)}>
          <h3
            className="mt-1 line-clamp-2 font-display text-body font-semibold leading-snug text-text-primary transition-colors duration-fast group-hover:text-accent"
            title={video.title}
          >
            {video.title}
          </h3>
        </Link>
        <p className="mt-1.5 text-caption text-text-secondary">
          {formatDate(video.created_at)}
          {video.duration > 0 && <span className="font-mono"> · {formatTimecode(video.duration)}</span>}
        </p>
        <div className={cn("mt-2.5 flex justify-center")}>
          <VideoStatusBadge status={video.status} />
        </div>
      </div>
    </article>
  );
}
