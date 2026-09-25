import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { PROCESSING_POLL_INTERVAL_MS, isTerminalVideoStatus } from "@/lib/constants";
import * as flashcardsService from "@/services/flashcards";
import type { VideoStatus } from "@/types/video";

/** Polls while `videoStatus` is non-terminal — see useTranscript.ts for why. */
export function useFlashcards(videoId: number, videoStatus?: VideoStatus) {
  return useQuery({
    queryKey: ["flashcards", videoId],
    queryFn: () => flashcardsService.getFlashcards(videoId),
    refetchInterval: videoStatus && !isTerminalVideoStatus(videoStatus) ? PROCESSING_POLL_INTERVAL_MS : false,
  });
}

export function useExportFlashcards(videoId: number) {
  return useMutation({
    mutationFn: () => flashcardsService.exportFlashcardsToAnki(videoId),
  });
}

/** Local (not persisted) front/back reveal + position state for the flashcard study view. */
export function useFlashcardStudy(total: number) {
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const [completed, setCompleted] = useState<Set<number>>(new Set());

  function goTo(nextIndex: number) {
    setIndex(Math.max(0, Math.min(total - 1, nextIndex)));
    setRevealed(false);
  }

  function next() {
    setCompleted((current) => new Set(current).add(index));
    goTo(index + 1);
  }

  function previous() {
    goTo(index - 1);
  }

  function reset() {
    setIndex(0);
    setRevealed(false);
    setCompleted(new Set());
  }

  return {
    index,
    revealed,
    completed,
    isFirst: index === 0,
    isLast: index === total - 1,
    reveal: () => setRevealed(true),
    hide: () => setRevealed(false),
    toggle: () => setRevealed((value) => !value),
    next,
    previous,
    goTo,
    reset,
  };
}
