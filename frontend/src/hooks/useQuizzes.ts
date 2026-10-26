import { useQuery } from "@tanstack/react-query";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as quizzesService from "@/services/quizzes";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useQuizzes(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["quizzes", videoId],
    queryFn: () => quizzesService.getQuizzes(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}
