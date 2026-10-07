import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import { AxiosError, AxiosHeaders } from "axios";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { useUpload } from "@/hooks/useUpload";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

/**
 * Uploading a video is the one action the entire product exists to
 * support - everything else (processing, search, quizzes) only
 * happens after this succeeds. useUpload (not the page around it)
 * owns all of that real logic: progress state, cancellation via a
 * real AbortController, and the error/success transitions - so it's
 * tested directly here rather than through UploadStudioPage's 3D
 * markup, which contributes no logic of its own.
 */
vi.mock("@/services/videos");

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
    id: 1,
    owner_id: 1,
    title: "clip.mp4",
    filename: "clip.mp4",
    language: "en",
    duration: 0,
    status: "uploaded",
    has_thumbnail: false,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderUseUpload() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const invalidateQueries = vi.spyOn(queryClient, "invalidateQueries");
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
  const rendered = renderHook(() => useUpload(), { wrapper });
  return { ...rendered, invalidateQueries };
}

describe("useUpload", () => {
  beforeEach(() => {
    vi.mocked(videosService.uploadVideo).mockReset();
  });

  it("starts idle", () => {
    const { result } = renderUseUpload();
    expect(result.current.stage).toBe("idle");
    expect(result.current.video).toBeNull();
  });

  it("tracks real upload progress, then reports success and invalidates the video list", async () => {
    const file = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    const uploadedVideo = makeVideo();

    vi.mocked(videosService.uploadVideo).mockImplementation(async (_file, options) => {
      options?.onProgress?.(50);
      options?.onProgress?.(100);
      return uploadedVideo;
    });

    const { result, invalidateQueries } = renderUseUpload();

    let returned: Video | null = null;
    await act(async () => {
      returned = await result.current.upload(file);
    });

    expect(returned).toEqual(uploadedVideo);
    expect(result.current.stage).toBe("success");
    expect(result.current.progress).toBe(100);
    expect(result.current.video).toEqual(uploadedVideo);
    expect(invalidateQueries).toHaveBeenCalled();
  });

  it("reaches the uploading stage with intermediate progress before completion", async () => {
    const file = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    let capturedOnProgress: ((percent: number) => void) | undefined;

    vi.mocked(videosService.uploadVideo).mockImplementation(
      (_file, options) =>
        new Promise((resolve) => {
          capturedOnProgress = options?.onProgress;
          // Never resolves within this test - we only assert the
          // in-flight "uploading" state before completion.
          void resolve;
        }),
    );

    const { result } = renderUseUpload();

    act(() => {
      void result.current.upload(file);
    });

    await waitFor(() => expect(result.current.stage).toBe("uploading"));

    act(() => capturedOnProgress?.(42));

    await waitFor(() => expect(result.current.progress).toBe(42));
    expect(result.current.stage).toBe("uploading");
    expect(result.current.fileName).toBe("clip.mp4");
  });

  it("aborts the real upload request when cancel is called", async () => {
    const file = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    let capturedSignal: AbortSignal | undefined;

    vi.mocked(videosService.uploadVideo).mockImplementation(
      (_file, options) =>
        new Promise(() => {
          capturedSignal = options?.signal;
        }),
    );

    const { result } = renderUseUpload();

    act(() => {
      void result.current.upload(file);
    });

    await waitFor(() => expect(capturedSignal).toBeDefined());
    expect(capturedSignal?.aborted).toBe(false);

    act(() => result.current.cancel());

    expect(capturedSignal?.aborted).toBe(true);
  });

  it("surfaces the server's real error message and never fakes success", async () => {
    const file = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    vi.mocked(videosService.uploadVideo).mockRejectedValue(
      axiosErrorWithResponse(413, { detail: "File too large" }),
    );

    const { result } = renderUseUpload();

    let returned: Video | null = makeVideo();
    await act(async () => {
      returned = await result.current.upload(file);
    });

    expect(returned).toBeNull();
    expect(result.current.stage).toBe("error");
    expect(result.current.error).toBe("File too large");
    expect(result.current.video).toBeNull();
  });

  it("reset returns to idle after a failed upload", async () => {
    const file = new File([new Uint8Array(10)], "clip.mp4", { type: "video/mp4" });
    vi.mocked(videosService.uploadVideo).mockRejectedValue(new Error("network down"));

    const { result } = renderUseUpload();
    await act(async () => {
      await result.current.upload(file);
    });
    expect(result.current.stage).toBe("error");

    act(() => result.current.reset());

    expect(result.current.stage).toBe("idle");
    expect(result.current.error).toBeNull();
  });
});
