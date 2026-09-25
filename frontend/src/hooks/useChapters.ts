import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as chaptersService from "@/services/chapters";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useChapters(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["chapters", videoId],
    queryFn: () => chaptersService.getChapters(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
