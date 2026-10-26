import { act, render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { useVideoPlayer, VideoPlayerProvider } from "@/hooks/useVideoPlayer";

/**
 * Regression coverage for the real bug: the provider attached its media
 * listeners in a mount-time effect, but the workspace mounts <video> only
 * after the media token resolves - so `videoRef.current` was null at that
 * point, no listener ever attached, duration stayed 0:00 and the play
 * overlay never went away. The element here mounts after the provider,
 * exactly like the real page.
 */
function Probe() {
  const player = useVideoPlayer();
  const [mounted, setMounted] = useState(false);
  return (
    <div>
      <button type="button" onClick={() => setMounted(true)}>
        mount
      </button>
      {mounted && <video data-testid="video" ref={player.attachVideo} />}
      <span data-testid="duration">{player.duration}</span>
      <span data-testid="playing">{String(player.isPlaying)}</span>
    </div>
  );
}

describe("VideoPlayerProvider", () => {
  it("picks up media events from a <video> that mounts after the provider", () => {
    render(
      <VideoPlayerProvider>
        <Probe />
      </VideoPlayerProvider>,
    );

    act(() => screen.getByRole("button", { name: "mount" }).click());
    const video = screen.getByTestId("video") as HTMLVideoElement;

    Object.defineProperty(video, "duration", { configurable: true, value: 25 });
    act(() => {
      video.dispatchEvent(new Event("loadedmetadata"));
      video.dispatchEvent(new Event("play"));
    });

    expect(screen.getByTestId("duration")).toHaveTextContent("25");
    expect(screen.getByTestId("playing")).toHaveTextContent("true");
  });
});
