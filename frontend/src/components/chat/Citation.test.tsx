import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { Citation } from "@/components/chat/Citation";
import * as videoPlayer from "@/hooks/useVideoPlayer";
import type { SearchResult } from "@/types/search";

function source(overrides: Partial<SearchResult> = {}): SearchResult {
  return {
    vector_id: "v-1",
    video_id: 7,
    chunk_index: 2,
    chunk_text: "Lạm phát là mức tăng chung của giá cả.",
    distance: 0.2,
    start_time: 83,
    end_time: 97.5,
    ...overrides,
  };
}

describe("Citation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("shows when the source was said and plays the video from there", async () => {
    const user = userEvent.setup();
    const player = { seek: vi.fn(), play: vi.fn() };
    vi.spyOn(videoPlayer, "useOptionalVideoPlayer").mockReturnValue(
      player as unknown as ReturnType<typeof videoPlayer.useOptionalVideoPlayer>,
    );

    render(<Citation index={1} source={source()} />);
    await user.click(screen.getByRole("button", { name: "1" }));

    expect(screen.getByText(/1:23 – 1:37/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /play from 1:23/i }));

    expect(player.seek).toHaveBeenCalledWith(83);
    expect(player.play).toHaveBeenCalled();
  });

  it("shows no time and no seek control for a source without a time span", async () => {
    const user = userEvent.setup();
    vi.spyOn(videoPlayer, "useOptionalVideoPlayer").mockReturnValue(
      { seek: vi.fn(), play: vi.fn() } as unknown as ReturnType<typeof videoPlayer.useOptionalVideoPlayer>,
    );

    render(<Citation index={1} source={source({ start_time: null, end_time: null })} />);
    await user.click(screen.getByRole("button", { name: "1" }));

    expect(screen.getByText(/Lạm phát là mức tăng/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /play from/i })).not.toBeInTheDocument();
  });

  it("renders without a player (outside the workspace) and offers no seek", async () => {
    const user = userEvent.setup();

    render(<Citation index={1} source={source()} />);
    await user.click(screen.getByRole("button", { name: "1" }));

    expect(screen.getByText(/1:23/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /play from/i })).not.toBeInTheDocument();
  });
});
