import { AxiosError, AxiosHeaders } from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

import { WorkspaceHeader } from "./WorkspaceHeader";

/**
 * Same gap as LibraryPage's delete flow: useDeleteVideo had no
 * onError/isError handling here either, so a failed delete from the
 * workspace header silently did nothing visible.
 */
vi.mock("@/services/videos");

const pushMock = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
}));

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

function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 7,
    owner_id: 2,
    title: "Workspace clip",
    filename: "clip.mp4",
    language: "en",
    duration: 90,
    status: "processed",
    has_thumbnail: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderHeader() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <WorkspaceHeader video={makeVideo()} />
    </QueryClientProvider>,
  );
}

describe("WorkspaceHeader - delete video", () => {
  beforeEach(() => {
    vi.mocked(videosService.deleteVideo).mockReset();
    pushMock.mockReset();
  });

  it("keeps the dialog open and shows the real error when delete fails, without navigating away", async () => {
    vi.mocked(videosService.deleteVideo).mockRejectedValue(
      axiosErrorWithResponse(500, { detail: "Could not delete this video right now." }),
    );

    const user = userEvent.setup();
    renderHeader();

    await user.click(screen.getByRole("button", { name: /delete video/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /delete video/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/could not delete this video right now/i);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(pushMock).not.toHaveBeenCalled();
  });

  it("navigates back to the library on a successful delete", async () => {
    vi.mocked(videosService.deleteVideo).mockResolvedValue(undefined);

    const user = userEvent.setup();
    renderHeader();

    await user.click(screen.getByRole("button", { name: /delete video/i }));
    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /delete video/i }));

    await waitFor(() => expect(pushMock).toHaveBeenCalledWith("/library"));
  });
});
