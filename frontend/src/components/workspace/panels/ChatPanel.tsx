"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { AIMessage } from "@/components/chat/AIMessage";
import { Icon } from "@/components/ui/Icon";
import { useChat } from "@/hooks/useChat";
import { cn } from "@/lib/utils";

const SUGGESTED_PROMPTS = [
  "What are the main points covered?",
  "Summarize the key takeaways.",
  "What was said about the main topic?",
];

export function ChatPanel({ videoId, videoTitle }: { videoId: number; videoTitle?: string }) {
  const { messages, send, isSending } = useChat(videoId);
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
    if (lastMessage?.role !== "assistant" || lastMessage.pending || lastMessage.status !== "answered") return;
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
        {messages.length === 0 ? (
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
              return (
                <div key={message.id} className="animate-mode-enter">
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
          Each question is answered independently — this conversation isn&apos;t saved.
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
