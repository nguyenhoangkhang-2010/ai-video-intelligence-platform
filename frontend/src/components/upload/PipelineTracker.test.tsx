import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { PipelineTracker } from "@/components/upload/PipelineTracker";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

/**
 * Regression coverage for the same bug class fixed in
 * ProcessingBanner: this is the screen a person watches immediately
 * after uploading, and it used to have no error branch at all for
 * either useVideo or useVideoProcessingJobs - a genuine fetch failure
 * rendered as "Starting…" frozen at stage 0 forever, indistinguishable
 * from the pipeline just being slow.
 */
vi.mock("@/services/videos");
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 10,
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

function renderTracker(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NovaAttentionProvider>{ui}</NovaAttentionProvider>
    </QueryClientProvider>,
  );
}

describe("PipelineTracker", () => {
  beforeEach(() => {
    vi.mocked(videosService.getVideo).mockReset();
    vi.mocked(videosService.getVideoProcessingJobs).mockReset();
  });

  it("shows a real error with retry, not a frozen 'Starting…', when the video fetch fails", async () => {
    vi.mocked(videosService.getVideo).mockRejectedValue(new Error("network down"));
    vi.mocked(videosService.getVideoProcessingJobs).mockResolvedValue([]);

    renderTracker(<PipelineTracker videoId={10} />);

    expect(await screen.findByText(/couldn't check processing status/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /retry/i })).toBeInTheDocument();
    expect(screen.queryByText(/starting…/i)).not.toBeInTheDocument();
  });

  it("shows a real error with retry when the jobs fetch fails", async () => {
    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo());
    vi.mocked(videosService.getVideoProcessingJobs).mockRejectedValue(new Error("network down"));

    renderTracker(<PipelineTracker videoId={10} />);

    expect(await screen.findByText(/couldn't check processing status/i)).toBeInTheDocument();
  });

  it("shows real stage progress once both fetches succeed", async () => {
    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo({ status: "processing" }));
    vi.mocked(videosService.getVideoProcessingJobs).mockResolvedValue([
      {
        id: 1,
        video_id: 10,
        job_type: "full_pipeline",
        status: "RUNNING",
        progress: 70,
        current_step: "Transcribing",
        started_at: "2026-01-01T00:00:00Z",
        finished_at: null,
        error_message: null,
      },
    ]);

    renderTracker(<PipelineTracker videoId={10} />);

    expect(await screen.findByText("Transcribing")).toBeInTheDocument();
  });
});
