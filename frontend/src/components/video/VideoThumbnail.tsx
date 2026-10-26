"use client";

import { useState } from "react";

import { useMediaToken } from "@/hooks/useVideos";
import { getVideoThumbnailUrl } from "@/services/videos";
import type { Video } from "@/types/video";

interface VideoThumbnailProps {
  video: Video;
  /**
   * Scale (px) of the placeholder glyph shown when no real frame is
   * available, so each caller can match its own surface size.
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
 *    a flat surface with a small film-frame glyph - "no real frame
 *    available", never dressed up as one.
 *
 * Also falls back to that same abstract surface if the real image URL
 * errors after being rendered (has_thumbnail can be briefly stale
 * relative to a delete/reprocess) - the fallback never pretends to be
 * an actual frame either way.
 */
export function VideoThumbnail({ video, patternSpacing = 18 }: VideoThumbnailProps) {
  const [imageFailed, setImageFailed] = useState(false);
  const isProcessing = video.status === "uploaded" || video.status === "processing";
  const mediaToken = useMediaToken(video.id, video.has_thumbnail && !imageFailed);

  if (video.has_thumbnail && !imageFailed && !mediaToken.isError) {
    if (!mediaToken.data) {
      return <div className="skeleton absolute inset-0" aria-hidden="true" />;
    }

    return (
      // Deliberate, not an oversight: this URL carries a short-lived auth
      // token as a query param (see getVideoThumbnailUrl), which
      // next/image's optimizer/proxy isn't a good fit for (see the module
      // docstring above for the full reasoning).
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={getVideoThumbnailUrl(video.id, mediaToken.data)}
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
      className="absolute inset-0 flex items-center justify-center bg-surface-sunken text-text-disabled"
      aria-hidden="true"
    >
      <svg width={patternSpacing * 2} height={patternSpacing * 2} viewBox="0 0 24 24" fill="none">
        <rect x="3" y="6" width="18" height="12" stroke="currentColor" strokeWidth="1.4" />
        <path d="M10 9.5v5l4.2-2.5z" fill="currentColor" />
      </svg>
    </div>
  );
}
