"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
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
    // Nova's "success" gesture as if it had.
    if (
      lastMessage?.role !== "assistant" ||
      lastMessage.pending ||
      lastMessage.status !== "answered" ||
      lastMessage.id.startsWith("hist-")
    )
      return;
    notice("success", 1400);
  }, [lastMessage?.id, lastMessage?.status, lastMessage?.pending, lastMessage?.role, notice]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!draft.trim()) return;
    void send(draft);
    setDraft("");
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex shrink-0 items-center gap-3 border-b border-text-primary/20 px-5 py-3">
        <SignalGlyph state={novaState} />
        <div className="min-w-0">
          <p className="text-body-sm font-semibold text-text-primary">
            Nova <span className="index-label ml-1 text-ai">assistant</span>
          </p>
          <p className="truncate text-caption text-text-secondary">
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
            <span className="flex h-12 w-12 items-center justify-center rounded-full border-[3px] border-ai bg-surface-elevated text-ai">
              <Icon name="chat" size={20} />
            </span>
            <div>
              <p className="font-display text-body-lg font-semibold text-text-primary">Ask this video anything</p>
              <p className="mt-1 max-w-[32ch] text-caption text-text-secondary">
                Answers are grounded in the transcript, with cited sources — not general knowledge.
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-1.5">
              {SUGGESTED_PROMPTS.map((prompt, index) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => void send(prompt)}
                  className="animate-mode-enter border border-text-primary/40 bg-surface-elevated px-3 py-1.5 text-caption text-text-secondary transition-colors duration-fast hover:border-ai hover:text-ai"
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
              return (
                <div key={message.id} className="relative animate-mode-enter">
                  <AIMessage
                    message={message}
                    onRetry={canRetry ? () => void send(precedingUserMessage!.content) : undefined}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="shrink-0 border-t border-text-primary/20 bg-surface p-3 sm:px-6">
        <div className="mx-auto flex max-w-2xl items-end gap-2 border border-text-primary/50 bg-surface-elevated p-1.5 transition-colors duration-fast focus-within:border-ai focus-within:shadow-[0_0_0_1px_rgb(var(--color-ai))]">
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
            className="flex h-9 w-9 shrink-0 items-center justify-center bg-ai text-ai-on transition-colors duration-fast hover:bg-ai-hover disabled:bg-surface-sunken disabled:text-text-disabled"
          >
            <Icon name="chevron-right" size={17} />
          </button>
        </div>
        <p className="mx-auto mt-1.5 max-w-2xl px-1 text-[11px] text-text-muted">
          Each question is answered independently, grounded only in this video — your past questions and answers are saved here so you can find them again.
        </p>
      </form>
    </div>
  );
}

/**
 * A cheap, non-3D indicator reflecting the same shared Nova state as
 * the ambient instance (see NovaAttentionContext): a tiny petrol dial
 * whose hand sweeps while Nova is thinking/searching and settles at
 * twelve once an answer lands - no second WebGL canvas needed.
 */
function SignalGlyph({ state }: { state: string }) {
  const active = state === "thinking" || state === "searching";
  const settled = state === "success" || state === "excited";
  return (
    <span
      className={cn(
        "relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full border-[3px] bg-surface-sunken transition-colors duration-base",
        settled ? "border-lume" : "border-ai",
      )}
      aria-hidden="true"
    >
      <span className={cn("absolute inset-0", active && "animate-spin")} style={{ animationDuration: "1.6s" }}>
        <span className="absolute left-1/2 top-[3px] h-[11px] w-[2px] -translate-x-1/2 bg-ai" />
      </span>
      <span className="h-1.5 w-1.5 rounded-full bg-text-primary" />
    </span>
  );
}
