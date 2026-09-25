import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as meetingsService from "@/services/meetings";

/**
 * Aggregated view backing the workspace Overview panel. Polls while
 * the video is still uploaded/processing (using the video status
 * embedded in its own response, so no external status prop is
 * needed) and stops once terminal — without this, opening Overview
 * before the pipeline finishes generating a summary/translation/quiz
 * would show them as permanently missing instead of catching up once
 * they're actually ready.
 */
export function useMeeting(videoId: number) {
  return useQuery({
    queryKey: ["meeting", videoId],
    queryFn: () => meetingsService.getMeeting(videoId),
    refetchInterval: (query) => {
      const status = query.state.data?.video.status;
      if (!status) return false;
      return isTerminalVideoStatus(status) ? false : PROCESSING_POLL_INTERVAL_MS;
    },
  });
}
