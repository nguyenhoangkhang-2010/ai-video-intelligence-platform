import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { VideoThumbnail } from "@/components/video/VideoThumbnail";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

vi.mock("@/services/videos", () => ({
  getVideoThumbnailUrl: (videoId: number, mediaToken: string) =>
    `http://api.test/videos/${videoId}/thumbnail?token=${mediaToken}`,
  getMediaToken: vi.fn(),
}));

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

function makeVideo(overrides: Partial<Video>): Video {
  return {
    id: 1,
    owner_id: 1,
    title: "clip.mp4",
    filename: "clip.mp4",
    language: "en",
    duration: 42,
    status: "processed",
    has_thumbnail: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("VideoThumbnail", () => {
  beforeEach(() => {
    vi.mocked(videosService.getMediaToken).mockReset();
    vi.mocked(videosService.getMediaToken).mockResolvedValue({ token: "t", expires_in: 300 });
  });

  it("renders the real extracted frame when has_thumbnail is true", async () => {
    const video = makeVideo({ id: 7, title: "clip.mp4", status: "processed", has_thumbnail: true });
    renderWithQueryClient(<VideoThumbnail video={video} />);

    const img = await screen.findByRole("img", { name: /representative frame from "clip.mp4"/i });
    expect(img).toHaveAttribute("src", "http://api.test/videos/7/thumbnail?token=t");
    expect(img).toHaveAttribute("loading", "lazy");
  });

  it("shows a skeleton while the media token for a real frame is still loading", () => {
    const video = makeVideo({ id: 7, status: "processed", has_thumbnail: true });
    const { container } = renderWithQueryClient(<VideoThumbnail video={video} />);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });

  it("shows a skeleton, never a fabricated frame, while still processing", () => {
    const { container } = renderWithQueryClient(
      <VideoThumbnail video={makeVideo({ status: "processing", has_thumbnail: false })} />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });

  it("shows the neutral abstract surface, not a skeleton, when there's no thumbnail and processing is done", () => {
    const { container } = renderWithQueryClient(
      <VideoThumbnail video={makeVideo({ status: "failed", has_thumbnail: false })} />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).not.toBeInTheDocument();
  });

  it("falls back to the abstract surface instead of a broken image if the real frame fails to load", async () => {
    const video = makeVideo({ id: 9, status: "processed", has_thumbnail: true });
    renderWithQueryClient(<VideoThumbnail video={video} />);

    const img = await screen.findByRole("img");
    fireEvent.error(img);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  it("falls back to the abstract surface, not an infinite skeleton, when the media token request fails", async () => {
    vi.mocked(videosService.getMediaToken).mockRejectedValue(new Error("network down"));
    const video = makeVideo({ id: 9, status: "processed", has_thumbnail: true });
    const { container } = renderWithQueryClient(<VideoThumbnail video={video} />);

    await waitFor(() => {
      expect(container.querySelector(".skeleton")).not.toBeInTheDocument();
    });
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
