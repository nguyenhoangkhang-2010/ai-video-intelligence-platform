import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as transcriptService from "@/services/transcripts";
import type { VideoStatus } from "@/types/video";

/**
 * `videoStatus` (the video's own real-time status, passed down from
 * useVideo by the caller) drives polling: while the pipeline is still
 * "uploaded"/"processing", this keeps refetching so a transcript that
 * finishes generating after the panel first loaded actually appears,
 * instead of the panel being stuck showing "not generated yet"
 * forever (see lib/constants.ts::isTerminalVideoStatus).
 */
export function useTranscript(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["transcript", videoId],
    queryFn: () => transcriptService.getTranscript(videoId),
    retry: (failureCount, error) => {
      // 404 means "not generated yet" (or the video simply has none) -
      // retrying won't change that; don't treat it as transient.
      const status = (error as { response?: { status?: number } })?.response?.status;
      if (status === 404) return false;
      return failureCount < 1;
    },
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
