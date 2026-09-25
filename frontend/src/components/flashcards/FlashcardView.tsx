"use client";

import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";
import type { Flashcard } from "@/types/flashcard";

interface FlashcardViewProps {
  card: Flashcard;
  revealed: boolean;
  onToggle: () => void;
}

export function FlashcardView({ card, revealed, onToggle }: FlashcardViewProps) {
  return (
    <div className="[perspective:1400px]">
      <button
        type="button"
        onClick={onToggle}
        aria-label={revealed ? "Show question" : "Show answer"}
        className={cn(
          "relative h-72 w-full rounded-2xl border border-border-strong bg-surface text-left shadow-glow-secondary transition-transform duration-slow ease-calm [transform-style:preserve-3d]",
          revealed && "[transform:rotateY(180deg)]",
        )}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 p-8 text-center [backface-visibility:hidden]">
          <span className="text-caption font-medium uppercase tracking-wide text-text-muted">Question</span>
          <p className="text-heading-sm font-medium leading-snug text-text-primary">{card.question}</p>
          <span className="absolute bottom-4 flex items-center gap-1 text-caption text-text-disabled">
            <Icon name="chevron-down" size={12} />
            Click to reveal
          </span>
        </div>

        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-atmosphere-muted p-8 text-center [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <span className="text-caption font-medium uppercase tracking-wide text-atmosphere">Answer</span>
          <p className="text-heading-sm font-medium leading-snug text-text-primary">{card.answer}</p>
        </div>
      </button>
    </div>
  );
}
