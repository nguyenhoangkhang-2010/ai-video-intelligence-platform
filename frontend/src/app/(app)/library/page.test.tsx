import { AxiosError, AxiosHeaders } from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

import LibraryPage from "./page";

function axiosErrorWithResponse(status: number, data: unknown): AxiosError {
  const error = new AxiosError("Request failed", String(status));
  error.response = {
    status,
    data,
    statusText: "",
    headers: {},
    config: { headers: new AxiosHeaders() },
  };
  return error;
}

/**
 * Regression coverage for the real gap found in the UX audit:
 * useDeleteVideo had no onError/isError handling anywhere it was
 * used, so a failed delete just silently closed the confirmation
 * dialog (via onSettled) with no visible sign the video was never
 * actually removed. Only the HTTP layer is mocked.
 */
vi.mock("@/services/videos");

function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 1,
    owner_id: 2,
    title: "Real clip",
    filename: "clip.mp4",
    language: "en",
    duration: 120,
    status: "processed",
    // false so no media-token fetch is needed for the thumbnail -
    // irrelevant to the delete-error behavior under test.
    has_thumbnail: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderLibraryPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <LibraryPage />
    </QueryClientProvider>,
  );
}

describe("LibraryPage - delete video", () => {
  beforeEach(() => {
    vi.mocked(videosService.listVideos).mockReset();
    vi.mocked(videosService.deleteVideo).mockReset();
  });

  // Two videos: a lone video renders only via FeaturedVideo (no delete
  // action at all), so the delete affordance (VideoRow's own menu) only
  // actually exists once there's a second, non-featured video.
  async function openDeleteConfirmationForSecondVideo(user: ReturnType<typeof userEvent.setup>) {
    vi.mocked(videosService.listVideos).mockResolvedValue([
      makeVideo({ id: 1, title: "Newest clip", created_at: "2026-01-02T00:00:00Z" }),
      makeVideo({ id: 2, title: "Older clip", created_at: "2026-01-01T00:00:00Z" }),
    ]);

    renderLibraryPage();

    await screen.findByText("Older clip");
    await user.click(screen.getByRole("button", { name: /video actions/i }));
    await user.click(screen.getByRole("menuitem", { name: /delete/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  }

  it("keeps the dialog open and shows the real error when delete fails", async () => {
    vi.mocked(videosService.deleteVideo).mockRejectedValue(
      axiosErrorWithResponse(500, { detail: "Could not delete this video right now." }),
    );

    const user = userEvent.setup();
    await openDeleteConfirmationForSecondVideo(user);

    await user.click(screen.getByRole("button", { name: /delete video/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not delete this video right now/i);
    // Still open, still showing the video it was about to delete.
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Older clip")).toBeInTheDocument();
  });

  it("closes the dialog and removes the video from the list on success", async () => {
    vi.mocked(videosService.deleteVideo).mockResolvedValue(undefined);

    const user = userEvent.setup();
    await openDeleteConfirmationForSecondVideo(user);

    await user.click(screen.getByRole("button", { name: /delete video/i }));

    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument());
    expect(screen.queryByText("Older clip")).not.toBeInTheDocument();
  });

  it("clears a previous error once the dialog is reopened for another video", async () => {
    vi.mocked(videosService.deleteVideo).mockRejectedValue(
      axiosErrorWithResponse(500, { detail: "Could not delete this video right now." }),
    );

    const user = userEvent.setup();
    await openDeleteConfirmationForSecondVideo(user);
    await user.click(screen.getByRole("button", { name: /delete video/i }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /video actions/i }));
    await user.click(screen.getByRole("menuitem", { name: /delete/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
