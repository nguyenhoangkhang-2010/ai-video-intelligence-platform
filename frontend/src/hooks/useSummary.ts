import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as summaryService from "@/services/summary";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useSummaries(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["summaries", videoId],
    queryFn: () => summaryService.getSummaries(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
