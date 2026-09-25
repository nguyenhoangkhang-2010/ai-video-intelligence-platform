import { useCallback, useState } from "react";

import { toApiError } from "@/lib/axios";
import * as chatService from "@/services/chat";
import type { ChatMessage } from "@/types/chat";

/**
 * Client-local chat transcript only — mirrors the backend's own
 * statelessness (see docs/api/rest_api.md, Search & RAG: "no
 * conversation history is persisted"). Refreshing the page or
 * revisiting the video starts a new, empty transcript; nothing here
 * should be read as a saved conversation.
 */
export function useChat(videoId: number) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);

  const send = useCallback(
    async (query: string) => {
      const trimmed = query.trim();
      if (!trimmed || isSending) return;

      const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: trimmed };
      const pendingId = crypto.randomUUID();
      setMessages((current) => [
        ...current,
        userMessage,
        { id: pendingId, role: "assistant", content: "", pending: true },
      ]);
      setIsSending(true);

      try {
        const result = await chatService.askVideo(videoId, trimmed);
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? {
                  id: pendingId,
                  role: "assistant",
                  content: result.answer ?? "",
                  status: result.status,
                  sources: result.sources,
                }
              : message,
          ),
        );
      } catch (error) {
        const apiError = toApiError(error);
        setMessages((current) =>
          current.map((message) =>
            message.id === pendingId
              ? { id: pendingId, role: "assistant", content: "", error: apiError.message }
              : message,
          ),
        );
      } finally {
        setIsSending(false);
      }
    },
    [videoId, isSending],
  );

  const clear = useCallback(() => setMessages([]), []);

  return { messages, send, clear, isSending };
}
