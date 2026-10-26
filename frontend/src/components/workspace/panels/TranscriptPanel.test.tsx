import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { TranscriptPanel } from "@/components/workspace/panels/TranscriptPanel";
import * as videoPlayer from "@/hooks/useVideoPlayer";
import * as transcriptService from "@/services/transcripts";
import type { Transcript } from "@/types/transcript";

vi.mock("@/services/transcripts");

const fakePlayer = {
  currentTime: 0,
  isPlaying: false,
  seek: vi.fn(),
  play: vi.fn(),
};

function transcript(overrides: Partial<Transcript> = {}): Transcript {
  return {
    id: 1,
    video_id: 7,
    language: "vi",
    text: "Xin chào mọi người. Hôm nay nói về lạm phát.",
    word_count: 9,
    created_at: "2026-01-01T00:00:00Z",
    segments: [
      { start: 0, end: 4.2, text: "Xin chào mọi người." },
      { start: 4.2, end: 71.5, text: "Hôm nay nói về lạm phát." },
    ],
    ...overrides,
  };
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <TranscriptPanel videoId={7} videoStatus="processed" />
    </QueryClientProvider>,
  );
}

describe("TranscriptPanel - timed segments", () => {
  beforeEach(() => {
    fakePlayer.currentTime = 0;
    fakePlayer.seek.mockReset();
    fakePlayer.play.mockReset();
    vi.spyOn(videoPlayer, "useOptionalVideoPlayer").mockReturnValue(
      fakePlayer as unknown as ReturnType<typeof videoPlayer.useOptionalVideoPlayer>,
    );
  });

  it("shows when each line was said and plays the video from a clicked line", async () => {
    const user = userEvent.setup();
    vi.mocked(transcriptService.getTranscript).mockResolvedValue(transcript());

    renderPanel();

    const line = await screen.findByRole("button", { name: /0:04.*lạm phát/i });
    expect(screen.getByText("0:00")).toBeInTheDocument();

    await user.click(line);

    expect(fakePlayer.seek).toHaveBeenCalledWith(4.2);
    expect(fakePlayer.play).toHaveBeenCalled();
  });

  it("marks the line being spoken right now", async () => {
    fakePlayer.currentTime = 10;
    vi.mocked(transcriptService.getTranscript).mockResolvedValue(transcript());

    renderPanel();

    const current = await screen.findByRole("button", { name: /lạm phát/i });
    expect(current).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: /xin chào/i })).not.toHaveAttribute("aria-current");
  });

  it("falls back to plain paragraphs, with no timestamps, for a transcript without segments", async () => {
    vi.mocked(transcriptService.getTranscript).mockResolvedValue(transcript({ segments: null }));

    renderPanel();

    expect(await screen.findByText(/Hôm nay nói về lạm phát/)).toBeInTheDocument();
    expect(screen.queryByRole("list", { name: /timed transcript/i })).not.toBeInTheDocument();
    expect(screen.queryByText("0:00")).not.toBeInTheDocument();
  });
});
