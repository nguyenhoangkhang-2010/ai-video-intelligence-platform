import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ScreenPanel } from "@/components/workspace/panels/ScreenPanel";
import * as videoPlayer from "@/hooks/useVideoPlayer";
import * as videosService from "@/services/videos";
import * as visualService from "@/services/visual";
import type { VisualSegment } from "@/types/visual";

vi.mock("@/services/visual", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@/services/visual")>()),
  getVisualSegments: vi.fn(),
}));
vi.mock("@/services/videos");

const fakePlayer = { currentTime: 0, isPlaying: false, seek: vi.fn(), play: vi.fn() };

function segment(overrides: Partial<VisualSegment>): VisualSegment {
  return {
    id: 1,
    video_id: 7,
    start_time: 0,
    end_time: 10,
    on_screen_text: "",
    description: "",
    speech_similarity: null,
    relation: "no-speech",
    has_frame: false,
    ...overrides,
  };
}

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ScreenPanel videoId={7} videoStatus="processed" />
    </QueryClientProvider>,
  );
}

describe("ScreenPanel", () => {
  beforeEach(() => {
    fakePlayer.currentTime = 0;
    fakePlayer.seek.mockReset();
    vi.spyOn(videoPlayer, "useOptionalVideoPlayer").mockReturnValue(
      fakePlayer as unknown as ReturnType<typeof videoPlayer.useOptionalVideoPlayer>,
    );
    vi.mocked(videosService.getMediaToken).mockResolvedValue({ token: "media-token" } as never);
  });

  it("shows on-screen text, description and how each scene relates to the speech", async () => {
    vi.mocked(visualService.getVisualSegments).mockResolvedValue([
      segment({ id: 1, on_screen_text: "Doanh thu +20%", description: "Biểu đồ cột.", relation: "illustrates" }),
      segment({ id: 2, start_time: 10, end_time: 30, description: "Cảnh phố đêm.", relation: "unrelated" }),
    ]);

    renderPanel();

    expect(await screen.findByText("Doanh thu +20%")).toBeInTheDocument();
    expect(screen.getByText("Biểu đồ cột.")).toBeInTheDocument();
    expect(screen.getByText("Matches speech")).toBeInTheDocument();
    expect(screen.getByText("B-roll")).toBeInTheDocument();
    expect(screen.getByText("2 scenes")).toBeInTheDocument();
  });

  it("loads keyframes with the media token and seeks from a scene", async () => {
    const user = userEvent.setup();
    vi.mocked(visualService.getVisualSegments).mockResolvedValue([
      segment({ id: 3, start_time: 42, description: "Slide.", has_frame: true }),
    ]);

    renderPanel();

    const image = await screen.findByRole("img", { name: "Slide." });
    expect(image.getAttribute("src")).toContain("/videos/7/visual-segments/3/frame");
    expect(image.getAttribute("src")).toContain("token=media-token");

    await user.click(screen.getByRole("button", { name: "Play from 0:42" }));
    expect(fakePlayer.seek).toHaveBeenCalledWith(42);
  });

  it("explains an empty result once processing is done", async () => {
    vi.mocked(visualService.getVisualSegments).mockResolvedValue([]);

    renderPanel();

    expect(await screen.findByText("Nothing read from the screen")).toBeInTheDocument();
  });
});
