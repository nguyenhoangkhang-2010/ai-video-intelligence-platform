"use client";

import { Icon } from "@/components/ui/Icon";
import { useOptionalVideoPlayer } from "@/hooks/useVideoPlayer";
import { cn, formatTimecode } from "@/lib/utils";

/**
 * "Jump to this moment": seeks the workspace player to `seconds` and
 * starts playback. Renders nothing when there is no time to seek to
 * (a video processed before chunk times were stored) or no player
 * around (e.g. outside the workspace), so callers can drop it in
 * unconditionally.
 */
export function SeekButton({
  seconds,
  className,
}: {
  seconds: number | null | undefined;
  className?: string;
}) {
  const player = useOptionalVideoPlayer();

  if (seconds === null || seconds === undefined || !player) return null;

  return (
    <button
      type="button"
      onClick={() => {
        player.seek(seconds);
        player.play();
      }}
      aria-label={`Play from ${formatTimecode(seconds)}`}
      className={cn(
        "inline-flex items-center gap-1 border border-text-primary/30 bg-surface-elevated px-1.5 py-0.5 font-mono text-caption text-text-primary transition-colors duration-fast hover:border-lume hover:bg-lume hover:text-lume-on",
        className,
      )}
    >
      <Icon name="play" size={10} />
      {formatTimecode(seconds)}
    </button>
  );
}
