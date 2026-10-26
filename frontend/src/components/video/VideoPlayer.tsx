"use client";

import { useRef, useState, type KeyboardEvent as ReactKeyboardEvent, type MouseEvent as ReactMouseEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { Spinner } from "@/components/ui/Spinner";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { cn, formatTimecode } from "@/lib/utils";
import type { Chapter } from "@/types/chapter";

const SKIP_SECONDS = 10;

interface VideoPlayerProps {
  src: string;
  title: string;
  chapters?: Chapter[];
  /** Fill the parent box instead of sizing itself (used inside the workspace dial). */
  fill?: boolean;
  /** The API's duration, shown until the <video> reports its own. */
  fallbackDuration?: number;
}

/**
 * Custom chrome over a native <video> element — deliberately not the
 * browser's default controls (which look identical across every
 * product) and not a third-party player library. Chapter markers on
 * the seek bar come from real Chapter data (start_time/end_time); no
 * timestamp is fabricated. Video is the visual anchor of the
 * workspace, so this stays dark/undecorated chrome around it rather
 * than a bordered "card".
 */
export function VideoPlayer({ src, title, chapters = [], fill = false, fallbackDuration = 0 }: VideoPlayerProps) {
  const player = useVideoPlayer();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [showControls, setShowControls] = useState(true);
  const [hasError, setHasError] = useState(false);
  const duration = player.duration || fallbackDuration;
  const progress = duration > 0 ? Math.min(100, (player.currentTime / duration) * 100) : 0;

  function handleSeekBarClick(event: ReactMouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / rect.width;
    player.seek(ratio * duration);
  }

  // Clicking anywhere in the player (the <video> element itself, or
  // the big play button) moves keyboard focus to the player wrapper
  // so Space/←/→/F/M work immediately after — a bare click on the
  // <video> element doesn't otherwise focus an ancestor container.
  function focusPlayer() {
    wrapperRef.current?.focus();
  }

  // Player-wide shortcuts (Space/←/→/F/M) once the player has focus -
  // skipped when the seek bar itself is focused (it already owns
  // ←/→ for fine-grained scrubbing) or when a native control
  // (button/range input) is focused, so its own default key behavior
  // isn't hijacked or double-fired.
  function handlePlayerKeyDown(event: ReactKeyboardEvent<HTMLDivElement>) {
    const target = event.target as HTMLElement;
    if (target.getAttribute("role") === "slider" || ["BUTTON", "INPUT"].includes(target.tagName)) return;

    if (event.key === " ") {
      event.preventDefault();
      player.togglePlay();
    } else if (event.key === "ArrowRight") {
      player.seek(player.currentTime + SKIP_SECONDS);
    } else if (event.key === "ArrowLeft") {
      player.seek(player.currentTime - SKIP_SECONDS);
    } else if (event.key.toLowerCase() === "f") {
      void player.videoRef.current?.requestFullscreen();
    } else if (event.key.toLowerCase() === "m") {
      player.toggleMute();
    }
  }

  return (
    <div
      ref={wrapperRef}
      role="group"
      aria-label={`Video player — ${title}`}
      tabIndex={0}
      onKeyDown={handlePlayerKeyDown}
      className={cn(
        "group/player relative overflow-hidden bg-text-primary outline-none focus-visible:ring-2 focus-visible:ring-accent",
        fill ? "h-full w-full" : "mx-auto aspect-video max-h-[42vh] w-auto max-w-full",
      )}
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => player.isPlaying && setShowControls(false)}
    >
      {!hasError && (
        <video
          ref={player.attachVideo}
          src={src}
          className="h-full w-full cursor-pointer"
          onClick={() => {
            player.togglePlay();
            focusPlayer();
          }}
          onError={() => setHasError(true)}
          playsInline
        />
      )}

      {hasError && (
        <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-surface-sunken">
          <Icon name="file-warning" size={24} />
          <p className="text-body-sm">This video couldn&apos;t be loaded.</p>
        </div>
      )}

      {player.isBuffering && !hasError && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <Spinner size={28} className="text-surface" />
        </div>
      )}

      {!player.isPlaying && !player.isBuffering && !hasError && (
        <button
          type="button"
          onClick={() => {
            player.togglePlay();
            focusPlayer();
          }}
          aria-label="Play"
          className="absolute inset-0 flex items-center justify-center bg-text-primary/25 transition-opacity duration-base"
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full border-[3px] border-text-primary bg-lume text-lume-on transition-transform duration-fast hover:scale-105">
            <Icon name="play" size={26} />
          </span>
        </button>
      )}

      <div
        className={cn(
          "absolute inset-x-0 bottom-0 flex flex-col gap-1.5 bg-text-primary/90 px-3 pb-2 pt-2 transition-opacity duration-base",
          showControls || !player.isPlaying ? "opacity-100" : "opacity-0",
        )}
      >
        <div
          role="slider"
          aria-label="Seek"
          aria-valuemin={0}
          aria-valuemax={duration}
          aria-valuenow={player.currentTime}
          aria-valuetext={`${formatTimecode(player.currentTime)} of ${formatTimecode(duration)}`}
          tabIndex={0}
          onClick={handleSeekBarClick}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight") player.seek(player.currentTime + 5);
            if (event.key === "ArrowLeft") player.seek(player.currentTime - 5);
          }}
          className="group/seek relative h-3 w-full cursor-pointer"
        >
          <div className="absolute top-1/2 h-1 w-full -translate-y-1/2 bg-surface/25">
            <div className="h-full bg-lume" style={{ width: `${progress}%` }} />
          </div>
          {chapters.map((chapter) => (
            <div
              key={chapter.id}
              title={chapter.title}
              className="absolute top-1/2 h-2.5 w-[2px] -translate-y-1/2 bg-atmosphere"
              style={{ left: `${duration ? (chapter.start_time / duration) * 100 : 0}%` }}
            />
          ))}
          <div
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-text-primary bg-lume opacity-0 transition-opacity duration-fast group-hover/seek:opacity-100"
            style={{ left: `${progress}%` }}
          />
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => player.seek(player.currentTime - SKIP_SECONDS)}
              aria-label={`Rewind ${SKIP_SECONDS} seconds`}
              className="hidden text-surface hover:text-lume sm:block"
            >
              <Icon name="skip-back" size={16} />
            </button>

            <button
              type="button"
              onClick={player.togglePlay}
              aria-label={player.isPlaying ? "Pause" : "Play"}
              className="text-surface hover:text-lume"
            >
              <Icon name={player.isPlaying ? "pause" : "play"} size={18} />
            </button>

            <button
              type="button"
              onClick={() => player.seek(player.currentTime + SKIP_SECONDS)}
              aria-label={`Forward ${SKIP_SECONDS} seconds`}
              className="hidden text-surface hover:text-lume sm:block"
            >
              <Icon name="skip-forward" size={16} />
            </button>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={player.toggleMute}
                aria-label={player.isMuted ? "Unmute" : "Mute"}
                className="text-surface hover:text-lume"
              >
                <Icon name={player.isMuted || player.volume === 0 ? "volume-mute" : "volume"} size={17} />
              </button>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={player.isMuted ? 0 : player.volume}
                onChange={(event) => player.setVolume(Number(event.target.value))}
                aria-label="Volume"
                className={cn("h-1 w-16 accent-lume", fill ? "hidden xl:block" : "hidden sm:block")}
              />
            </div>

            <span className="whitespace-nowrap font-mono text-caption text-surface/80">
              {formatTimecode(player.currentTime)} / {formatTimecode(duration)}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className={cn("max-w-[200px] truncate text-caption text-surface/80", fill ? "hidden" : "hidden sm:block")} title={title}>
              {title}
            </span>
            <button
              type="button"
              onClick={() => player.videoRef.current?.requestFullscreen()}
              aria-label="Fullscreen"
              className="text-surface hover:text-lume"
            >
              <Icon name="fullscreen" size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
