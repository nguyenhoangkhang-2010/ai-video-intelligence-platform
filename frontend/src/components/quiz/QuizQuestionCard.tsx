"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { cn, parseQuizOptions, quizTypeLabel } from "@/lib/utils";
import type { Quiz } from "@/types/quiz";

interface QuizQuestionCardProps {
  quiz: Quiz;
  index: number;
  /** Fired once, the first time this question is answered/revealed — lets the panel show a real "X of N" session progress indicator. */
  onAnswered?: () => void;
  /** The focused, one-question-at-a-time presentation (QuizPanel) - larger, un-boxed, the question itself as the focal object rather than one card in a list. */
  focused?: boolean;
}

/**
 * Self-check only — the backend has no submit/score/attempt-history
 * endpoint (see docs/api/rest_api.md, Quizzes section), so "correct"
 * is a client-side comparison against the answer already returned
 * alongside the question, not a fabricated scoring API.
 */
export function QuizQuestionCard({ quiz, index, onAnswered, focused }: QuizQuestionCardProps) {
  const [selected, setSelected] = useState<string | null>(null);
  const [revealed, setRevealed] = useState(false);

  const options = quiz.type === "multiple_choice" ? parseQuizOptions(quiz.options) : ["True", "False"];
  const isChoiceType = quiz.type === "multiple_choice" || quiz.type === "true_false";

  function reveal() {
    if (!revealed) onAnswered?.();
    setRevealed(true);
  }

  function choose(option: string) {
    if (revealed) return;
    setSelected(option);
    reveal();
  }

  return (
    <div
      className={cn(
        "animate-slide-up",
        focused
          ? "flex w-full flex-col"
          : "rounded-lg border border-border bg-surface p-4 transition-colors duration-fast hover:border-border-strong",
      )}
    >
      <div className={cn("mb-3 flex items-center gap-2", focused && "justify-center")}>
        {!focused && (
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-surface-elevated font-mono text-[11px] text-text-secondary">
            {index + 1}
          </span>
        )}
        <span className="text-caption font-medium uppercase tracking-wide text-text-muted">
          {quizTypeLabel(quiz.type)}
        </span>
      </div>

      <p
        className={cn(
          "leading-relaxed text-text-primary",
          focused
            ? "mb-6 text-center text-heading font-medium sm:text-heading-lg"
            : "mb-3.5 text-body-sm font-medium",
        )}
      >
        {quiz.question}
      </p>

      {isChoiceType ? (
        <div className={cn("flex flex-col gap-2", focused ? "mx-auto w-full max-w-md" : "gap-1.5")}>
          {options.map((option) => {
            const isSelected = selected === option;
            const isCorrectOption = option.trim().toLowerCase() === quiz.answer.trim().toLowerCase();
            return (
              <button
                key={option}
                type="button"
                onClick={() => choose(option)}
                disabled={revealed}
                className={cn(
                  "flex items-center justify-between rounded border text-left transition-colors duration-fast",
                  focused ? "px-4 py-3 text-body" : "px-3 py-2 text-body-sm",
                  !revealed && "border-border-strong hover:border-accent hover:bg-surface-hover",
                  revealed && isCorrectOption && "border-success/40 bg-success-muted text-text-primary",
                  revealed && isSelected && !isCorrectOption && "border-error/40 bg-error-muted text-text-primary",
                  revealed && !isSelected && !isCorrectOption && "border-border text-text-muted",
                )}
              >
                <span>{option}</span>
                {revealed && isCorrectOption && <Icon name="check" size={15} className="text-success" />}
                {revealed && isSelected && !isCorrectOption && <Icon name="close" size={15} className="text-error" />}
              </button>
            );
          })}
        </div>
      ) : (
        <div className={cn(focused && "mx-auto flex w-full max-w-md flex-col items-center")}>
          {!revealed ? (
            <button
              type="button"
              onClick={reveal}
              className="rounded border border-border-strong bg-surface-elevated px-3 py-1.5 text-body-sm text-text-secondary transition-colors duration-fast hover:border-accent hover:text-accent"
            >
              Reveal answer
            </button>
          ) : (
            <div className="flex w-full items-start gap-2 rounded border border-success/40 bg-success-muted px-3 py-2 text-body-sm text-text-primary">
              <Icon name="check" size={15} className="mt-0.5 shrink-0 text-success" />
              {quiz.answer}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
