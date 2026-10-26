import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as visualService from "@/services/visual";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useVisualSegments(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["visual-segments", videoId],
    queryFn: () => visualService.getVisualSegments(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
