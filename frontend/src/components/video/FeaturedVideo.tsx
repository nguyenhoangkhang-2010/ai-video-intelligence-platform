import Link from "next/link";

import { DialRing } from "@/components/dial/DialRing";
import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { dialToneFor } from "@/components/video/VideoDial";
import { VideoThumbnail } from "@/components/video/VideoThumbnail";
import { ROUTES } from "@/lib/constants";
import { formatRelativeTime, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

/**
 * The library's lead piece - the most recent upload, presented like
 * the watch on the winder's centre cushion: a large dial with the real
 * extracted frame set into the face, next to its engraved details.
 * Shows a real frame only when one exists (see VideoThumbnail).
 */
export function FeaturedVideo({ video }: { video: Video }) {
  return (
    <Link
      href={ROUTES.video(video.id)}
      className="group grid grid-cols-1 items-center gap-8 border-y-2 border-text-primary py-8 md:grid-cols-[minmax(0,320px)_1fr] md:gap-12"
    >
      <div className="mx-auto aspect-square w-full max-w-[320px]">
        <DialRing progress={1} tone={dialToneFor(video)} ticks={60} caseWidth={4} emphasized>
          <span className="absolute inset-[15%] overflow-hidden rounded-full bg-surface">
            <VideoThumbnail video={video} patternSpacing={22} />
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-full bg-lume text-lume-on transition-transform duration-base group-hover:scale-110">
                <Icon name="play" size={22} />
              </span>
            </span>
          </span>
        </DialRing>
      </div>

      <div className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <p className="index-label text-accent">Most recent</p>
          <VideoStatusBadge status={video.status} />
        </div>
        <h2 className="font-display text-display font-semibold leading-tight text-text-primary" title={video.title}>
          {video.title}
        </h2>
        <dl className="grid max-w-md grid-cols-2 border-t border-text-primary/30 pt-4">
          <div>
            <dt className="index-label text-text-muted">Added</dt>
            <dd className="mt-1 text-body-sm text-text-primary">{formatRelativeTime(video.created_at)}</dd>
          </div>
          {video.duration > 0 && (
            <div>
              <dt className="index-label text-text-muted">Runs</dt>
              <dd className="mt-1 font-mono text-body-sm text-text-primary">{formatTimecode(video.duration)}</dd>
            </div>
          )}
        </dl>
        <span className="mt-1 inline-flex w-fit items-center gap-2 text-body-sm font-semibold text-text-primary">
          <span className="border-b-2 border-lume pb-0.5 transition-colors duration-fast group-hover:text-accent">
            Open workspace
          </span>
          <Icon name="arrow-right" size={15} />
        </span>
      </div>
    </Link>
  );
}
