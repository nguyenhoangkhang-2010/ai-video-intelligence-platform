"use client";

import { useState } from "react";

import { getVideoThumbnailUrl } from "@/services/videos";
import type { Video } from "@/types/video";

interface VideoThumbnailProps {
  video: Video;
  /**
   * Spacing (px) of the decorative scan-line pattern shown when no
   * real frame is available yet, so each caller can match its own
   * existing density (VideoRow's compact row vs. FeaturedVideo's
   * large editorial surface) instead of this component forcing one.
   */
  patternSpacing?: number;
}

/**
 * Renders this video's real, ffmpeg-extracted representative frame
 * when one exists, with three honest states - never a stock image,
 * never a frame guessed for a video that doesn't have one:
 *
 *  - has_thumbnail: the real frame. Plain <img>, not next/image - the
 *    URL carries a short-lived auth token as a query param (the same
 *    pattern getVideoStreamUrl already uses for <video>, since an
 *    <img> can't attach an Authorization header), which next/image's
 *    optimizer/proxy isn't a good fit for.
 *  - still processing (no thumbnail yet, status is uploaded/processing):
 *    the shared .skeleton shimmer (globals.css) - signals "generating",
 *    never a placeholder dressed up as a frame.
 *  - no thumbnail and done processing (extraction failed, or this
 *    video predates the thumbnail feature and hasn't been backfilled):
 *    the same abstract scan-line surface this library has always used
 *    for "no real frame available."
 *
 * Also falls back to that same abstract surface if the real image URL
 * errors after being rendered (has_thumbnail can be briefly stale
 * relative to a delete/reprocess) - the fallback never pretends to be
 * an actual frame either way.
 */
export function VideoThumbnail({ video, patternSpacing = 18 }: VideoThumbnailProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const isProcessing = video.status === "uploaded" || video.status === "processing";

  if (video.has_thumbnail && !imageFailed) {
    return (
      // Deliberate, not an oversight: this URL carries a short-lived auth
      // token as a query param (see getVideoThumbnailUrl), which
      // next/image's optimizer/proxy isn't a good fit for (see the module
      // docstring above for the full reasoning).
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={getVideoThumbnailUrl(video.id)}
        alt={`Representative frame from "${video.title}"`}
        loading="lazy"
        decoding="async"
        onError={() => setImageFailed(true)}
        className="absolute inset-0 h-full w-full object-cover transition-transform duration-base ease-calm group-hover:scale-105"
      />
    );
  }

  if (isProcessing) {
    return <div className="skeleton absolute inset-0" aria-hidden="true" />;
  }

  return (
    <div
      className="absolute inset-0 opacity-[0.06] transition-opacity duration-base group-hover:opacity-[0.12]"
      style={{
        backgroundImage:
          `repeating-linear-gradient(115deg, rgb(var(--color-ai)) 0px, rgb(var(--color-ai)) 1px, transparent 1px, transparent ${patternSpacing}px)`,
      }}
      aria-hidden="true"
    />
  );
}
