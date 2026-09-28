"use client";

import { useEffect } from "react";

import { FlashcardView } from "@/components/flashcards/FlashcardView";
import { useAccentSlotClaim } from "@/components/3d/workspace3d/AccentSlotContext";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Icon } from "@/components/ui/Icon";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useExportFlashcards, useFlashcards, useFlashcardStudy } from "@/hooks/useFlashcards";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { VideoStatus } from "@/types/video";

export function FlashcardsPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const flashcards = useFlashcards(videoId, videoStatus);
  const exportFlashcards = useExportFlashcards(videoId);
  const total = flashcards.data?.length ?? 0;
  const study = useFlashcardStudy(total);
  // Claims the shared Workspace accent slot only while the real
  // completion accent is actually mounted below (see
  // AccentSlotContext.tsx) - the same real condition the accent's own
  // render guard uses.
  useAccentSlotClaim(study.completed.size === total && total > 0);

  useEffect(() => {
    study.reset();
    // Reset the study session if the underlying card set changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [total]);

  // Keyboard study controls: Left/Right to navigate, Space/Enter to flip.
  // Skipped while focus is inside a form control so it never hijacks
  // typing elsewhere in the workspace.
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA"].includes(target.tagName)) return;
      if (event.key === "ArrowRight" && !study.isLast) study.next();
      if (event.key === "ArrowLeft" && !study.isFirst) study.previous();
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        study.toggle();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [study.index, study.isFirst, study.isLast]);

  if (flashcards.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-4">
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (flashcards.isError) {
    return <ErrorState error={toApiError(flashcards.error)} onRetry={() => flashcards.refetch()} compact />;
  }

  if (!flashcards.data || flashcards.data.length === 0) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <ProcessingState
          icon="flashcard"
          title="Flashcards are being generated…"
          description="This updates automatically the moment they're ready — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="flashcard"
        title="No flashcards available"
        description="Processing finished without producing flashcards for this video."
      />
    );
  }

  const card = flashcards.data[study.index];
  const allCompleted = study.completed.size === total && total > 0;

  if (!card) return null;

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="flashcard"
        label="Flashcards"
        meta={<span>{study.completed.size} of {total} reviewed</span>}
        actions={
          <Button variant="ghost" size="sm" onClick={() => exportFlashcards.mutate()} isLoading={exportFlashcards.isPending}>
            <Icon name="download" size={14} />
            Export to Anki
          </Button>
        }
      />

      <div className="flex flex-1 flex-col items-center justify-center gap-5 overflow-y-auto p-6">
        <div key={study.index} className="w-full max-w-md animate-rise">
          <FlashcardView card={card} revealed={study.revealed} onToggle={study.toggle} />
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={study.previous}
            disabled={study.isFirst}
            aria-label="Previous card"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-border-strong text-text-secondary enabled:hover:border-atmosphere enabled:hover:text-atmosphere disabled:opacity-30"
          >
            <Icon name="chevron-left" size={16} />
          </button>

          <span className="font-mono text-caption text-text-muted">
            {study.index + 1} / {total}
          </span>

          <div className="flex gap-1">
            {flashcards.data.map((_, index) => (
              <span
                key={index}
                className={cn(
                  "h-1.5 w-1.5 rounded-full",
                  index === study.index
                    ? "bg-atmosphere"
                    : study.completed.has(index)
                      ? "bg-success/60"
                      : "bg-border-strong",
                )}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={study.next}
            disabled={study.isLast}
            aria-label="Next card"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-border-strong text-text-secondary enabled:hover:border-atmosphere enabled:hover:text-atmosphere disabled:opacity-30"
          >
            <Icon name="chevron-right" size={16} />
          </button>
        </div>

        <p className="text-caption text-text-disabled">Space to flip · Arrow keys to navigate</p>

        {allCompleted && (
          <div className="flex animate-rise flex-col items-center gap-2">
            {/*
             * rs_flashcards.glb (ui-3d/README.md) - its real "Float"
             * clip as a small completion accent, shown only once
             * `study.completed` (real session state, every card this
             * visit has actually been flipped) reaches the total -
             * never a decorative default, only a genuine "you finished
             * these" moment.
             */}
            <Workspace3DObject model="flashcards" loopClip="Float" className="h-20 w-20" />
            <div className="flex items-center gap-2 rounded-full border border-warm/30 bg-warm-muted px-3 py-1.5 text-caption font-medium text-warm">
              <Icon name="check" size={13} />
              You&apos;ve reviewed all {total} cards
            </div>
          </div>
        )}

        {exportFlashcards.isError && (
          <p className="text-caption text-error">{toApiError(exportFlashcards.error).message}</p>
        )}
      </div>
    </div>
  );
}
