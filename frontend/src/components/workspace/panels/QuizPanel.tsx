"use client";

import { useState } from "react";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Icon } from "@/components/ui/Icon";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { QuizQuestionCard } from "@/components/quiz/QuizQuestionCard";
import { useAccentSlotClaim } from "@/components/3d/workspace3d/AccentSlotContext";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useQuizzes } from "@/hooks/useQuizzes";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { VideoStatus } from "@/types/video";

const RING_RADIUS = 15;
const RING_CIRCUMFERENCE = 2 * Math.PI * RING_RADIUS;

/** A real circular progress ring — session-answered count / total, the same honest number the dots below already show, just a second legible form of it. */
function ProgressRing({ answered, total }: { answered: number; total: number }) {
  const fraction = total > 0 ? answered / total : 0;
  return (
    <svg width="36" height="36" viewBox="0 0 36 36" className="-rotate-90" aria-hidden="true">
      <circle cx="18" cy="18" r={RING_RADIUS} fill="none" strokeWidth="3" className="stroke-surface-elevated" />
      <circle
        cx="18"
        cy="18"
        r={RING_RADIUS}
        fill="none"
        strokeWidth="3"
        strokeLinecap="round"
        className="stroke-atmosphere transition-[stroke-dashoffset] duration-slow ease-calm"
        strokeDasharray={RING_CIRCUMFERENCE}
        strokeDashoffset={RING_CIRCUMFERENCE * (1 - fraction)}
      />
    </svg>
  );
}

/**
 * "Understanding Mode" — one question at a time, the same focused
 * study rhythm as Flashcards (shared ecosystem, not two unrelated
 * features), rather than a scrollable form of every question at once.
 * Progress is real session state (which questions have actually been
 * answered this visit), never a persisted score - the backend has no
 * attempt-history endpoint.
 */
export function QuizPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const quizzes = useQuizzes(videoId, videoStatus);
  const [index, setIndex] = useState(0);
  const [answered, setAnswered] = useState<Set<number>>(new Set());
  // Real client-side correctness from THIS question's own answer
  // reveal (see QuizQuestionCard - never a fabricated score), driving
  // a brief rs_quiz_card.glb reaction accent. `reactionKey` changes on
  // every reveal so the one-shot clip replays even if the same
  // correct/wrong value repeats back to back.
  const [reaction, setReaction] = useState<{ correct: boolean; key: number } | null>(null);
  // Claims the shared Workspace accent slot only while a real reaction
  // is actually mounted below (see AccentSlotContext.tsx).
  useAccentSlotClaim(reaction !== null);

  if (quizzes.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  if (quizzes.isError) {
    return <ErrorState error={toApiError(quizzes.error)} onRetry={() => quizzes.refetch()} compact />;
  }

  if (!quizzes.data || quizzes.data.length === 0) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <ProcessingState
          icon="quiz"
          title="Quiz questions are being generated…"
          description="This updates automatically the moment they're ready — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="quiz"
        title="No quiz available"
        description="Processing finished without producing quiz questions for this video."
      />
    );
  }

  const total = quizzes.data.length;
  const quiz = quizzes.data[index];
  const isFirst = index === 0;
  const isLast = index === total - 1;
  const allAnswered = answered.size === total;

  if (!quiz) return null;

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="quiz"
        label="Understanding Mode"
        meta={
          <span className="flex items-center gap-2">
            <ProgressRing answered={answered.size} total={total} />
            {answered.size} of {total} answered
          </span>
        }
      />

      <div className="flex flex-1 flex-col items-center justify-center gap-6 overflow-y-auto p-6">
        <div key={quiz.id} className="relative w-full max-w-lg animate-rise">
          <QuizQuestionCard
            quiz={quiz}
            index={index}
            focused
            onAnswered={(wasCorrect) => {
              setAnswered((current) => new Set(current).add(index));
              if (wasCorrect !== undefined) {
                setReaction((current) => ({ correct: wasCorrect, key: (current?.key ?? 0) + 1 }));
              }
            }}
          />
          {/*
           * rs_quiz_card.glb (ui-3d/README.md) - a small, secondary
           * reaction accent playing its real Answer_Correct/
           * Answer_Wrong clip once per reveal, driven entirely by the
           * same client-side correctness check the card itself already
           * makes (never a fabricated score). Positioned beside the
           * question, not over it, so it never blocks reading the real
           * answer state the card already shows.
           */}
          {reaction && (
            <Workspace3DObject
              key={reaction.key}
              model="quizCard"
              playClip={reaction.correct ? "Answer_Correct" : "Answer_Wrong"}
              playKey={reaction.key}
              className="pointer-events-none absolute -right-4 -top-4 hidden h-20 w-20 sm:block lg:-right-24 lg:h-24 lg:w-24"
            />
          )}
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIndex((current) => Math.max(0, current - 1))}
            disabled={isFirst}
            aria-label="Previous question"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-border-strong text-text-secondary enabled:hover:border-atmosphere enabled:hover:text-atmosphere disabled:opacity-30"
          >
            <Icon name="chevron-left" size={16} />
          </button>

          <span className="font-mono text-caption text-text-muted">
            {index + 1} / {total}
          </span>

          <div className="flex gap-1">
            {quizzes.data.map((_, i) => (
              <span
                key={i}
                className={cn(
                  "h-1.5 w-1.5 rounded-full transition-colors duration-base",
                  i === index ? "bg-atmosphere" : answered.has(i) ? "bg-success/60" : "bg-border-strong",
                )}
              />
            ))}
          </div>

          <button
            type="button"
            onClick={() => setIndex((current) => Math.min(total - 1, current + 1))}
            disabled={isLast}
            aria-label="Next question"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-border-strong text-text-secondary enabled:hover:border-atmosphere enabled:hover:text-atmosphere disabled:opacity-30"
          >
            <Icon name="chevron-right" size={16} />
          </button>
        </div>

        {allAnswered && (
          <div className="flex animate-rise items-center gap-2 rounded-full border border-warm/30 bg-warm-muted px-3 py-1.5 text-caption font-medium text-warm">
            <Icon name="check" size={13} />
            You&apos;ve answered all {total} questions
          </div>
        )}
      </div>
    </div>
  );
}
