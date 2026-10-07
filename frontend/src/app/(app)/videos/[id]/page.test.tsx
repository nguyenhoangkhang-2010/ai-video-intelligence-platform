import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import * as chaptersService from "@/services/chapters";
import * as flashcardsService from "@/services/flashcards";
import * as meetingsService from "@/services/meetings";
import * as quizzesService from "@/services/quizzes";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

import VideoWorkspacePage from "./page";

/**
 * Regression coverage for the real, reported bug: clicking a video
 * never actually showed the player. Root cause (see the session's
 * investigation) was an infrastructure issue (a stale running API
 * process never picking up the media-token route), not a code defect
 * - but tracing it surfaced a real, separate gap this test locks in:
 * if the media-token fetch itself fails, the page used to show an
 * infinite loading skeleton with no error and no way to retry. These
 * tests cover the three real states of the video-player area:
 * loading, the real player once a token resolves, and a real error
 * with a retry affordance when the token fetch fails.
 */
vi.mock("next/navigation", () => ({
  useParams: () => ({ id: "15" }),
  useRouter: () => ({ push: vi.fn() }),
}));
vi.mock("@/services/videos");
vi.mock("@/services/chapters");
vi.mock("@/services/quizzes");
vi.mock("@/services/meetings");
vi.mock("@/services/flashcards");

function makeVideo(overrides: Partial<Video> = {}): Video {
  return {
    id: 15,
    owner_id: 2,
    title: "Real clip",
    filename: "clip.mp4",
    language: "en",
    duration: 120,
    status: "processed",
    has_thumbnail: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderPage(ui: ReactElement = <VideoWorkspacePage />) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NovaAttentionProvider>{ui}</NovaAttentionProvider>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  // OverviewPanel (the default initial tab) fetches this aggregate via
  // useMeeting - without mocking it, this would be a REAL,
  // test-environment-leaking network call to whatever NEXT_PUBLIC_API_URL
  // points at, which happened to succeed/fail depending on whether a
  // real dev backend was reachable. Mocked here for every test in this
  // file so none of them depend on network reachability.
  vi.mocked(meetingsService.getMeeting).mockReset().mockRejectedValue(new Error("not mocked for this test"));
  vi.mocked(flashcardsService.getFlashcards).mockReset().mockRejectedValue(new Error("not mocked for this test"));
});

describe("VideoWorkspacePage - video player states", () => {
  beforeEach(() => {
    vi.mocked(videosService.getVideo).mockReset();
    vi.mocked(videosService.getMediaToken).mockReset();
    vi.mocked(videosService.getVideoStreamUrl).mockReset();
    vi.mocked(chaptersService.getChapters).mockReset().mockResolvedValue([]);
  });

  it("renders the real video element once the media token resolves, with a URL built from it", async () => {
    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo());
    vi.mocked(videosService.getMediaToken).mockResolvedValue({ token: "real-media-token", expires_in: 300 });
    vi.mocked(videosService.getVideoStreamUrl).mockImplementation(
      (videoId, token) => `http://api.test/videos/${videoId}/stream?token=${token}`,
    );

    renderPage();

    const video = await screen.findByLabelText(/video player/i);
    const source = video.querySelector("video");
    expect(source).toHaveAttribute("src", "http://api.test/videos/15/stream?token=real-media-token");
  });

  it("shows a real error with retry, not an infinite skeleton, when the media token request fails", async () => {
    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo());
    vi.mocked(videosService.getMediaToken).mockRejectedValue(new Error("network down"));

    renderPage();

    await waitFor(() => expect(screen.queryByLabelText(/video player/i)).not.toBeInTheDocument());
    expect(await screen.findByRole("button", { name: /try again|retry/i })).toBeInTheDocument();
  });

  it("retrying after a media-token failure re-fetches and can recover", async () => {
    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo());
    vi.mocked(videosService.getMediaToken)
      .mockRejectedValueOnce(new Error("network down"))
      .mockResolvedValueOnce({ token: "recovered-token", expires_in: 300 });
    vi.mocked(videosService.getVideoStreamUrl).mockImplementation(
      (videoId, token) => `http://api.test/videos/${videoId}/stream?token=${token}`,
    );

    renderPage();

    const retryButton = await screen.findByRole("button", { name: /try again|retry/i });
    retryButton.click();

    const video = await screen.findByLabelText(/video player/i);
    const source = video.querySelector("video");
    expect(source).toHaveAttribute("src", "http://api.test/videos/15/stream?token=recovered-token");
  });
});

describe("VideoWorkspacePage - quiz progress survives switching tabs", () => {
  beforeEach(() => {
    vi.mocked(videosService.getVideo).mockReset();
    vi.mocked(videosService.getMediaToken).mockReset();
    vi.mocked(videosService.getVideoStreamUrl).mockReset();
    vi.mocked(videosService.getVideoProcessingJobs).mockReset().mockResolvedValue([]);
    vi.mocked(chaptersService.getChapters).mockReset().mockResolvedValue([]);
    vi.mocked(quizzesService.getQuizzes).mockReset();

    vi.mocked(videosService.getVideo).mockResolvedValue(makeVideo());
    vi.mocked(videosService.getMediaToken).mockResolvedValue({ token: "t", expires_in: 300 });
    vi.mocked(videosService.getVideoStreamUrl).mockReturnValue("http://api.test/videos/15/stream?token=t");
    vi.mocked(quizzesService.getQuizzes).mockResolvedValue([
      { id: 1, video_id: 15, type: "true_false", question: "Is this real?", answer: "True", options: null },
    ]);
  });

  it("keeps the quiz panel mounted (progress intact) after switching away and back", async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(await screen.findByRole("button", { name: "Study" }));
    await user.click(await screen.findByRole("button", { name: "Quiz" }));

    const trueOption = await screen.findByRole("button", { name: "True" });
    await user.click(trueOption);
    expect(await screen.findByText(/1 of 1 answered/i)).toBeInTheDocument();

    // Switch away to a fully different panel, then back.
    await user.click(await screen.findByRole("button", { name: "Watch" }));
    await user.click(await screen.findByRole("button", { name: "Overview" }));
    await user.click(await screen.findByRole("button", { name: "Study" }));
    await user.click(await screen.findByRole("button", { name: "Quiz" }));

    expect(await screen.findByText(/1 of 1 answered/i)).toBeInTheDocument();
  });
});
