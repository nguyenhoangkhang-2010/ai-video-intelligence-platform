"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { useAccentSlotClaim } from "@/components/3d/workspace3d/AccentSlotContext";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { AIMessage } from "@/components/chat/AIMessage";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Spinner";
import { useChat } from "@/hooks/useChat";
import { cn } from "@/lib/utils";

const SUGGESTED_PROMPTS = [
  "What are the main points covered?",
  "Summarize the key takeaways.",
  "What was said about the main topic?",
];

export function ChatPanel({ videoId, videoTitle }: { videoId: number; videoTitle?: string }) {
  const { messages, send, isSending, isHistoryLoading } = useChat(videoId);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastMessage = messages[messages.length - 1];
  // A brief rs_ai_answer.glb accent next to the answer that just
  // arrived - `key` changes each time a real assistant message
  // finishes (see the effect below), and the accent itself hides again
  // a few seconds later so it reads as a one-time reaction to this
  // specific answer, not a permanent fixture competing with Nova's own
  // header signal glyph.
  const [answerAccent, setAnswerAccent] = useState<{ messageId: string; key: number } | null>(null);
  // Claims the shared Workspace accent slot only while a real answer
  // accent is actually mounted below (see AccentSlotContext.tsx).
  useAccentSlotClaim(answerAccent !== null);
  // Drives the single, product-wide Nova entity (see NovaAmbient) -
  // this panel doesn't own a Nova of its own, it's one of several
  // places that can tell the same living Nova what's happening.
  const { state: novaState, notice } = useNovaAttention();

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (isSending) notice("thinking");
  }, [isSending, notice]);

  useEffect(() => {
    // `hist-*` ids come from useChat's one-time seed of this user's
    // past turns (see toMessages there) - a real answer, but not one
    // that just happened this session, so it must never re-trigger
    // Nova's "success" gesture or the answer accent as if it had.
    if (
      lastMessage?.role !== "assistant" ||
      lastMessage.pending ||
      lastMessage.status !== "answered" ||
      lastMessage.id.startsWith("hist-")
    )
      return;
    notice("success", 1400);
    // Stays next to the latest answered message indefinitely - no
    // fixed-duration hide timer, which was fragile either way (too
    // short and a person could miss the accent entirely, too long and
    // it lingers after they've moved on). It naturally disappears from
    // THIS message the moment a newer one finishes and takes its
    // place, since `showAnswerAccent` only ever matches the single
    // most-recently-answered message id.
    setAnswerAccent((current) => ({ messageId: lastMessage.id, key: (current?.key ?? 0) + 1 }));
  }, [lastMessage?.id, lastMessage?.status, lastMessage?.pending, lastMessage?.role, notice]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    void send(draft);
    setDraft("");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-2.5 border-b border-border px-4 py-3">
        <SignalGlyph state={novaState} />
        <div className="min-w-0">
          <p className="text-body-sm font-semibold text-text-primary">
            Nova <span className="font-normal text-text-muted">— Video Intelligence Assistant</span>
          </p>
          <p className="truncate text-caption text-text-muted">
            {videoTitle ? `Grounded in “${videoTitle}”` : "Grounded in this video's transcript"}
          </p>
        </div>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 sm:px-6">
        {isHistoryLoading ? (
          // A brief real load of this user's own past turns for this
          // video (see useChat.ts) - shown instead of the empty state
          // so a returning conversation doesn't flash "Ask this video
          // anything" for a moment before its real history appears.
          <div className="mx-auto flex max-w-2xl flex-col gap-4">
            <Skeleton className="ml-auto h-8 w-2/5" />
            <Skeleton className="h-16 w-3/4" />
          </div>
        ) : messages.length === 0 ? (
          <div className="mx-auto flex h-full max-w-xl flex-col items-center justify-center gap-4 text-center">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-ai-muted text-ai">
              <Icon name="chat" size={20} />
            </span>
            <div>
              <p className="text-body-sm font-medium text-text-primary">Ask this video anything</p>
              <p className="mt-1 max-w-[32ch] text-caption text-text-muted">
                Answers are grounded in the transcript, with cited sources — not general knowledge.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-1.5">
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => void send(prompt)}
                  className="animate-mode-enter rounded-full border border-border-strong bg-surface px-3 py-1.5 text-caption text-text-secondary transition-colors duration-fast hover:border-ai-border hover:text-ai"
                  style={{ animationDelay: `${index * 60}ms` }}
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-2xl flex-col gap-4">
            {messages.map((message, index) => {
              const precedingUserMessage = messages[index - 1];
              const canRetry =
                message.role === "assistant" &&
                Boolean(message.error) &&
                precedingUserMessage?.role === "user";
              const showAnswerAccent = answerAccent?.messageId === message.id;
              return (
                <div key={message.id} className="relative animate-mode-enter">
                  <AIMessage
                    message={message}
                    onRetry={canRetry ? () => void send(precedingUserMessage!.content) : undefined}
                  />
                  {/*
                   * rs_ai_answer.glb (ui-3d/README.md) - a small,
                   * secondary accent (Nova, in the header above, is
                   * still the primary AI presence) playing its real
                   * "Answer" clip once when this specific message
                   * finishes, then hiding again - not a permanent
                   * fixture that would compete with Nova for
                   * attention.
                   */}
                  {showAnswerAccent && (
                    <Workspace3DObject
                      key={answerAccent.key}
                      model="aiAnswer"
                      playClip="Answer"
                      playKey={answerAccent.key}
                      className="mt-1 h-16 w-28 animate-mode-enter opacity-90"
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="shrink-0 border-t border-border p-3 sm:px-6">
        <div className="mx-auto flex max-w-2xl items-end gap-2 rounded-lg border border-border-strong bg-surface-sunken p-1.5 transition-colors duration-fast focus-within:border-accent">
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSubmit(event);
              }
            }}
            placeholder="Ask a question about this video…"
            rows={1}
            className="max-h-28 flex-1 resize-none bg-transparent px-2 py-1.5 text-body-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none"
          />
          <button
            type="submit"
            disabled={!draft.trim() || isSending}
            aria-label="Send message"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-accent text-accent-on transition-colors duration-fast hover:bg-accent-hover disabled:bg-surface-elevated disabled:text-text-disabled"
          >
            <Icon name="chevron-right" size={17} />
          </button>
        </div>
        <p className="mx-auto mt-1.5 max-w-2xl px-1 text-[11px] text-text-disabled">
          Each question is answered independently, grounded only in this video — your past questions and answers are saved here so you can find them again.
        </p>
      </form>
    </div>
  );
}

/**
 * A cheap, non-3D indicator reflecting the same shared Nova state as
 * the ambient instance in the corner of the screen (see
 * NovaAttentionContext) - this panel doesn't spin up a second WebGL
 * canvas just to show "Nova is thinking" locally; a live pulse on the
 * same intelligence-color signal does the job.
 */
function SignalGlyph({ state }: { state: string }) {
  const active = state === "thinking" || state === "searching";
  const settled = state === "success" || state === "excited";
  return (
    <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-ai-muted" aria-hidden="true">
      {active && <span className="absolute inset-0 animate-ping rounded-full bg-ai/30" />}
      <span
        className={cn(
          "h-2 w-2 rounded-full bg-ai transition-transform duration-base",
          settled && "scale-125",
        )}
      />
    </span>
  );
}
