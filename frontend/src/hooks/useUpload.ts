import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";

import { videoKeys } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import * as videosService from "@/services/videos";
import type { Video } from "@/types/video";

export type UploadStage = "idle" | "uploading" | "processing" | "success" | "error";

interface UploadState {
  stage: UploadStage;
  progress: number;
  fileName: string | null;
  error: string | null;
  video: Video | null;
}

const initialState: UploadState = {
  stage: "idle",
  progress: 0,
  fileName: null,
  error: null,
  video: null,
};

/**
 * Drives the upload flow: uploading (byte progress) -> processing
 * (the backend has already started the async pipeline by the time
 * POST /videos/upload resolves - see docs/api/rest_api.md) -> success.
 * "processing" here just means "handed off"; actual pipeline progress
 * is tracked separately on the video's detail page via useVideo's
 * polling.
 */
export function useUpload() {
  const queryClient = useQueryClient();
  const [state, setState] = useState<UploadState>(initialState);
  const abortRef = useRef<AbortController | null>(null);

  const upload = useCallback(
    async (file: File) => {
      abortRef.current = new AbortController();
      setState({ stage: "uploading", progress: 0, fileName: file.name, error: null, video: null });

      try {
        const video = await videosService.uploadVideo(file, {
          signal: abortRef.current.signal,
          onProgress: (percent) => {
            setState((current) => ({
              ...current,
              stage: percent >= 100 ? "processing" : "uploading",
              progress: percent,
            }));
          },
        });

        queryClient.invalidateQueries({ queryKey: videoKeys.list() });
        setState({ stage: "success", progress: 100, fileName: file.name, error: null, video });
        return video;
      } catch (error) {
        setState({
          stage: "error",
          progress: 0,
          fileName: file.name,
          error: toApiError(error).message,
          video: null,
        });
        return null;
      }
    },
    [queryClient],
  );

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const reset = useCallback(() => setState(initialState), []);

  return { ...state, upload, cancel, reset };
}
