import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProcessingBanner } from "@/components/workspace/ProcessingBanner";
import * as processingService from "@/services/processing";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

/**
 * Regression coverage for a real bug found while tracing the video-
 * playback issue: this banner only ever destructured `.data` from
 * useVideoProcessingJobs, never `.isError` - so a genuine fetch
 * failure (not just "still processing") looked identical to normal
 * in-progress state: "Processing video… 0%", frozen, forever, with no
 * error message and no way to retry.
 */
vi.mock("@/services/videos");
vi.mock("@/services/processing");

function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 1,
    owner_id: 1,
    title: "clip.mp4",
    filename: "clip.mp4",
    language: "en",
    duration: 42,
    status: "processing",
    has_thumbnail: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

describe("ProcessingBanner", () => {
  beforeEach(() => {
    vi.mocked(videosService.getVideoProcessingJobs).mockReset();
  });

  it("shows a real error with retry, not a frozen 0% progress bar, when the jobs fetch fails", async () => {
    vi.mocked(videosService.getVideoProcessingJobs).mockRejectedValue(new Error("network down"));

    renderWithQueryClient(<ProcessingBanner video={makeVideo({ status: "processing" })} />);

    expect(await screen.findByText(/couldn't load processing status/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    expect(screen.queryByText(/processing video…/i)).not.toBeInTheDocument();
  });

  it("shows real progress once the jobs fetch succeeds", async () => {
    vi.mocked(videosService.getVideoProcessingJobs).mockResolvedValue([
      {
        id: 1,
        video_id: 1,
        job_type: "full_pipeline",
        status: "RUNNING",
        progress: 42,
        current_step: "Transcribing",
        started_at: "2026-01-01T00:00:00Z",
        finished_at: null,
        error_message: null,
      },
    ]);

    renderWithQueryClient(<ProcessingBanner video={makeVideo({ status: "processing" })} />);

    expect(await screen.findByText("Transcribing")).toBeInTheDocument();
    expect(screen.getByText("42%")).toBeInTheDocument();
  });

  it("renders nothing once the video has actually finished processing", () => {
    const { container } = renderWithQueryClient(<ProcessingBanner video={makeVideo({ status: "processed" })} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("offers a real retry for a failed job and calls the retry endpoint with that job's id", async () => {
    const failedJob = {
      id: 20,
      video_id: 1,
      job_type: "full_pipeline",
      status: "FAILED" as const,
      progress: 100,
      current_step: "Failed",
      started_at: "2026-01-01T00:00:00Z",
      finished_at: "2026-01-01T00:01:00Z",
      error_message: "open() got an unexpected keyword argument 'metadata_errors'",
    };
    vi.mocked(videosService.getVideoProcessingJobs).mockResolvedValue([failedJob]);
    vi.mocked(processingService.retryProcessingJob).mockResolvedValue({ ...failedJob, status: "PENDING" });
    const user = userEvent.setup();

    renderWithQueryClient(<ProcessingBanner video={makeVideo({ status: "failed" })} />);

    await user.click(await screen.findByRole("button", { name: /retry processing/i }));

    await waitFor(() => expect(processingService.retryProcessingJob).toHaveBeenCalledWith(20));
  });
});
