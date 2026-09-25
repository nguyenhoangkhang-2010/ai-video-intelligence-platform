"use client";

import { Citation } from "@/components/chat/Citation";
import { Icon } from "@/components/ui/Icon";
import type { ChatMessage } from "@/types/chat";

function ThinkingIndicator() {
  return (
    <div className="flex items-center gap-1.5 text-ai">
      <span className="flex gap-1">
        {[0, 1, 2].map((dot) => (
          <span
            key={dot}
            className="h-1.5 w-1.5 rounded-full bg-current"
            style={{ animation: `pulse 1.2s ease-in-out ${dot * 0.15}s infinite` }}
          />
        ))}
      </span>
      <span className="text-caption text-text-muted">Analyzing the transcript…</span>
    </div>
  );
}

function statusCopy(status: ChatMessage["status"]): { icon: "info" | "alert"; text: string } | null {
  switch (status) {
    case "no_embeddings":
      return { icon: "info", text: "This video hasn't finished processing for search yet — try again shortly." };
    case "no_relevant_chunks":
      return { icon: "alert", text: "Nothing in this video's transcript closely matches that question." };
    case "empty_query":
      return { icon: "alert", text: "Ask a question to get started." };
    default:
      return null;
  }
}

export function AIMessage({ message, onRetry }: { message: ChatMessage; onRetry?: () => void }) {
  if (message.role === "user") {
    return (
      <div className="flex animate-slide-up justify-end">
        <div className="max-w-[85%] rounded-lg rounded-tr-sm bg-surface-elevated px-3.5 py-2 text-body-sm text-text-primary">
          {message.content}
        </div>
      </div>
    );
  }

  // Assistant message — the primary content of this panel, given
  // visual priority over the user's own question (see brief: "not a
  // ChatGPT clone" — grounded answers are the point, not a bubble
  // exchange).
  return (
    <div className="flex animate-slide-up items-start gap-2.5">
      <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-ai-muted text-ai">
        <Icon name="chat" size={13} />
      </span>
      <div className="min-w-0 flex-1">
        {message.pending && <ThinkingIndicator />}

        {message.error && (
          <div className="flex flex-col items-start gap-1.5">
            <div className="flex items-start gap-1.5 text-body-sm text-error">
              <Icon name="alert" size={15} className="mt-0.5 shrink-0" />
              {message.error}
            </div>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="ml-[21px] flex items-center gap-1.5 rounded border border-border-strong px-2 py-1 text-caption font-medium text-text-secondary transition-colors duration-fast hover:border-accent hover:text-accent"
              >
                <Icon name="refresh" size={12} />
                Retry
              </button>
            )}
          </div>
        )}

        {!message.pending && !message.error && message.status && statusCopy(message.status) && (
          <div className="flex items-start gap-1.5 text-body-sm text-text-secondary">
            <Icon name={statusCopy(message.status)!.icon} size={15} className="mt-0.5 shrink-0 text-text-muted" />
            {statusCopy(message.status)!.text}
          </div>
        )}

        {!message.pending && !message.error && message.status === "answered" && (
          <div>
            <p className="whitespace-pre-wrap text-body leading-relaxed text-text-primary">{message.content}</p>
            {message.sources && message.sources.length > 0 && (
              <div className="mt-3 border-t border-border pt-2.5">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="text-caption font-medium uppercase tracking-wide text-ai">Evidence</span>
                  {message.sources.map((source, index) => (
                    <Citation key={source.vector_id} index={index + 1} source={source} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
