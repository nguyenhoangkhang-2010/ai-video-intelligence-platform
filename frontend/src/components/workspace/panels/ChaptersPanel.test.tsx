import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ChaptersPanel } from "@/components/workspace/panels/ChaptersPanel";
import * as videoPlayer from "@/hooks/useVideoPlayer";
import * as chaptersService from "@/services/chapters";
import type { Chapter } from "@/types/chapter";

vi.mock("@/services/chapters");

const fakePlayer = {
  currentTime: 0,
  isPlaying: false,
  seek: vi.fn(),
  play: vi.fn(),
};

const chapters: Chapter[] = [
  { id: 1, video_id: 7, title: "Mở đầu", start_time: 0, end_time: 30, summary: null },
  { id: 2, video_id: 7, title: "Lạm phát là gì", start_time: 30, end_time: 290, summary: "Định nghĩa." },
  { id: 3, video_id: 7, title: "Kết luận", start_time: 290, end_time: 300, summary: null },
];

function renderPanel() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={queryClient}>
      <ChaptersPanel videoId={7} videoStatus="processed" />
    </QueryClientProvider>,
  );
}

describe("ChaptersPanel - narrative map", () => {
  beforeEach(() => {
    fakePlayer.currentTime = 0;
    fakePlayer.seek.mockReset();
    vi.spyOn(videoPlayer, "useVideoPlayer").mockReturnValue(
      fakePlayer as unknown as ReturnType<typeof videoPlayer.useVideoPlayer>,
    );
    vi.mocked(chaptersService.getChapters).mockResolvedValue(chapters);
  });

  it("sizes segments by duration without overflowing the row", async () => {
    renderPanel();

    const segment = await screen.findByRole("button", { name: "Lạm phát là gì, 0:30" });
    expect(segment.style.flexGrow).toBe("260");
    expect(segment.style.flexBasis).toBe("0px");
    expect(segment.style.width).toBe("");
    // A 10 s chapter in a 300 s video still gets a visible share.
    expect(screen.getByRole("button", { name: "Kết luận, 4:50" }).style.flexGrow).toBe("10");
  });

  it("labels each segment and marks the playing one", async () => {
    fakePlayer.currentTime = 100;
    renderPanel();

    const segment = await screen.findByRole("button", { name: "Lạm phát là gì, 0:30" });
    expect(segment).toHaveAttribute("aria-current", "true");
    expect(segment).toHaveTextContent("02");
    expect(screen.getByText("Định nghĩa.")).toBeInTheDocument();
  });

  it("opens hover details below the bar and seeks on click", async () => {
    const user = userEvent.setup();
    renderPanel();

    const segment = await screen.findByRole("button", { name: "Mở đầu, 0:00" });
    const details = segment.lastElementChild as HTMLElement;
    expect(details.className).toContain("top-full");
    expect(details.className).not.toContain("-translate-y-full");

    await user.click(segment);
    expect(fakePlayer.seek).toHaveBeenCalledWith(0);
  });
});
