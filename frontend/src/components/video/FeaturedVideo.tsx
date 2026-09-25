import Link from "next/link";

import { Icon } from "@/components/ui/Icon";
import { VideoStatusBadge } from "@/components/ui/StatusBadge";
import { ROUTES } from "@/lib/constants";
import { formatRelativeTime, formatTimecode } from "@/lib/utils";
import type { Video } from "@/types/video";

/**
 * The library's editorial lead — the most recent upload, given real
 * visual weight instead of sitting as one more tile in a uniform
 * grid. No thumbnail exists (the API has none), so the media surface
 * is an honestly abstract, generative-looking pattern — never dressed
 * up to look like a real video frame or waveform.
 */
export function FeaturedVideo({ video }: { video: Video }) {
  return (
    <Link
      href={ROUTES.video(video.id)}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-surface transition-colors duration-base hover:border-border-strong md:flex-row"
    >
      <div className="relative aspect-video shrink-0 overflow-hidden md:aspect-auto md:w-[46%]">
        <div
          className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_20%,rgb(var(--color-surface-elevated))_0%,rgb(var(--color-surface-sunken))_75%)]"
          aria-hidden="true"
        />
        <div
          className="absolute inset-0 opacity-[0.07] transition-opacity duration-base group-hover:opacity-[0.12]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(115deg, rgb(var(--color-ai)) 0px, rgb(var(--color-ai)) 1px, transparent 1px, transparent 34px)",
          }}
          aria-hidden="true"
        />
        <span className="absolute left-4 top-4 rounded-full bg-bg/60 backdrop-blur-[2px]">
          <VideoStatusBadge status={video.status} />
        </span>
        <span className="absolute inset-0 flex items-center justify-center">
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-bg/60 text-text-primary backdrop-blur-sm transition-transform duration-base group-hover:scale-105">
            <Icon name="play" size={26} />
          </span>
        </span>
      </div>

      <div className="flex flex-1 flex-col justify-center gap-3 p-7 md:p-9">
        <p className="text-label font-medium uppercase tracking-[0.14em] text-ai">Most recent</p>
        <h2 className="font-display text-heading-lg font-semibold leading-snug text-text-primary" title={video.title}>
          {video.title}
        </h2>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-body-sm text-text-muted">
          <span>{formatRelativeTime(video.created_at)}</span>
          {video.duration > 0 && (
            <span className="font-mono">{formatTimecode(video.duration)}</span>
          )}
        </div>
        <span className="mt-2 inline-flex w-fit items-center gap-1.5 text-body-sm font-medium text-text-primary transition-colors duration-fast group-hover:text-accent-hover">
          Open workspace
          <Icon name="chevron-right" size={15} />
        </span>
      </div>
    </Link>
  );
}
