import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { VideoThumbnail } from "@/components/video/VideoThumbnail";
import type { Video } from "@/types/video";

vi.mock("@/services/videos", () => ({
  getVideoThumbnailUrl: (videoId: number) => `http://api.test/videos/${videoId}/thumbnail?token=t`,
}));

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
  it("renders the real extracted frame when has_thumbnail is true", () => {
    const video = makeVideo({ id: 7, title: "clip.mp4", status: "processed", has_thumbnail: true });
    render(<VideoThumbnail video={video} />);

    const img = screen.getByRole("img", { name: /representative frame from "clip.mp4"/i });
    expect(img).toHaveAttribute("src", "http://api.test/videos/7/thumbnail?token=t");
    expect(img).toHaveAttribute("loading", "lazy");
  });

  it("shows a skeleton, never a fabricated frame, while still processing", () => {
    const { container } = render(
      <VideoThumbnail video={makeVideo({ status: "processing", has_thumbnail: false })} />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).toBeInTheDocument();
  });

  it("shows the neutral abstract surface, not a skeleton, when there's no thumbnail and processing is done", () => {
    const { container } = render(
      <VideoThumbnail video={makeVideo({ status: "failed", has_thumbnail: false })} />,
    );

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(container.querySelector(".skeleton")).not.toBeInTheDocument();
  });

  it("falls back to the abstract surface instead of a broken image if the real frame fails to load", () => {
    const video = makeVideo({ id: 9, status: "processed", has_thumbnail: true });
    render(<VideoThumbnail video={video} />);

    const img = screen.getByRole("img");
    fireEvent.error(img);

    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });
});
