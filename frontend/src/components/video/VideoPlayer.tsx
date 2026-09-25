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
export function VideoPlayer({ src, title, chapters = [] }: VideoPlayerProps) {
  const player = useVideoPlayer();
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [showControls, setShowControls] = useState(true);
  const [hasError, setHasError] = useState(false);
  const progress = player.duration > 0 ? (player.currentTime / player.duration) * 100 : 0;

  function handleSeekBarClick(event: ReactMouseEvent<HTMLDivElement>) {
    const rect = event.currentTarget.getBoundingClientRect();
    const ratio = (event.clientX - rect.left) / rect.width;
    player.seek(ratio * player.duration);
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
      className="group/player relative aspect-video w-full overflow-hidden rounded-2xl bg-black outline-none focus-visible:ring-2 focus-visible:ring-accent/60"
      onMouseEnter={() => setShowControls(true)}
      onMouseLeave={() => player.isPlaying && setShowControls(false)}
    >
      {!hasError && (
        <video
          ref={player.videoRef}
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
        <div className="flex h-full w-full flex-col items-center justify-center gap-2 text-text-muted">
          <Icon name="file-warning" size={24} />
          <p className="text-body-sm">This video couldn&apos;t be loaded.</p>
        </div>
      )}

      {player.isBuffering && !hasError && (
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <Spinner size={28} className="text-text-primary/80" />
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
          className="absolute inset-0 flex items-center justify-center bg-black/20 transition-opacity duration-base"
        >
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-bg/70 text-text-primary backdrop-blur-sm transition-transform duration-fast hover:scale-105">
            <Icon name="play" size={26} />
          </span>
        </button>
      )}

      <div
        className={cn(
          "absolute inset-x-0 bottom-0 flex flex-col gap-2 bg-gradient-to-t from-black/85 via-black/40 to-transparent px-4 pb-3 pt-10 transition-opacity duration-base",
          showControls || !player.isPlaying ? "opacity-100" : "opacity-0",
        )}
      >
        <div
          role="slider"
          aria-label="Seek"
          aria-valuemin={0}
          aria-valuemax={player.duration}
          aria-valuenow={player.currentTime}
          aria-valuetext={`${formatTimecode(player.currentTime)} of ${formatTimecode(player.duration)}`}
          tabIndex={0}
          onClick={handleSeekBarClick}
          onKeyDown={(event) => {
            if (event.key === "ArrowRight") player.seek(player.currentTime + 5);
            if (event.key === "ArrowLeft") player.seek(player.currentTime - 5);
          }}
          className="group/seek relative h-3 w-full cursor-pointer"
        >
          <div className="absolute top-1/2 h-1 w-full -translate-y-1/2 rounded-full bg-white/20">
            <div className="h-full rounded-full bg-accent" style={{ width: `${progress}%` }} />
          </div>
          {chapters.map((chapter) => (
            <div
              key={chapter.id}
              title={chapter.title}
              className="absolute top-1/2 h-2 w-[3px] -translate-y-1/2 rounded-full bg-text-primary/50"
              style={{ left: `${player.duration ? (chapter.start_time / player.duration) * 100 : 0}%` }}
            />
          ))}
          <div
            className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent opacity-0 shadow-sm transition-opacity duration-fast group-hover/seek:opacity-100"
            style={{ left: `${progress}%` }}
          />
        </div>

        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => player.seek(player.currentTime - SKIP_SECONDS)}
              aria-label={`Rewind ${SKIP_SECONDS} seconds`}
              className="hidden text-text-primary hover:text-accent sm:block"
            >
              <Icon name="skip-back" size={16} />
            </button>

            <button
              type="button"
              onClick={player.togglePlay}
              aria-label={player.isPlaying ? "Pause" : "Play"}
              className="text-text-primary hover:text-accent"
            >
              <Icon name={player.isPlaying ? "pause" : "play"} size={18} />
            </button>

            <button
              type="button"
              onClick={() => player.seek(player.currentTime + SKIP_SECONDS)}
              aria-label={`Forward ${SKIP_SECONDS} seconds`}
              className="hidden text-text-primary hover:text-accent sm:block"
            >
              <Icon name="skip-forward" size={16} />
            </button>

            <div className="flex items-center gap-1.5">
              <button
                type="button"
                onClick={player.toggleMute}
                aria-label={player.isMuted ? "Unmute" : "Mute"}
                className="text-text-primary hover:text-accent"
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
                className="hidden h-1 w-16 accent-accent sm:block"
              />
            </div>

            <span className="font-mono text-caption text-text-secondary">
              {formatTimecode(player.currentTime)} / {formatTimecode(player.duration)}
            </span>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden max-w-[200px] truncate text-caption text-text-secondary sm:block" title={title}>
              {title}
            </span>
            <button
              type="button"
              onClick={() => player.videoRef.current?.requestFullscreen()}
              aria-label="Fullscreen"
              className="text-text-primary hover:text-accent"
            >
              <Icon name="fullscreen" size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
