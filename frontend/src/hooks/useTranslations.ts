import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as translationsService from "@/services/translations";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useTranslations(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["translations", videoId],
    queryFn: () => translationsService.getTranslations(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
