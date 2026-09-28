import { useQuery } from "@tanstack/react-query";
import { useCallback, useEffect, useRef, useState } from "react";

import { toApiError } from "@/lib/axios";
import * as chatService from "@/services/chat";
import type { ChatHistoryEntry, ChatMessage } from "@/types/chat";

function toMessages(entry: ChatHistoryEntry): ChatMessage[] {
  return [
    { id: `hist-${entry.id}-q`, role: "user", content: entry.question },
    {
      id: `hist-${entry.id}-a`,
      role: "assistant",
      content: entry.answer,
      status: "answered",
      sources: entry.sources,
    },
  ];
}

/**
 * Seeded once from this user's own persisted history for the video
 * (see app/services/chat_history.py — a genuinely answered turn is
 * recorded server-side the moment `askVideo` returns it), then
 * appended to locally as new turns are sent. Retrieval/generation
 * itself is still stateless per call (see docs/api/rest_api.md,
 * Search & RAG) — this hook only restores what already happened, it
 * never feeds prior turns back into a new question.
 */
export function useChat(videoId: number) {
  const history = useQuery({
    queryKey: ["chatHistory", videoId],
    queryFn: () => chatService.getChatHistory(videoId),
  });
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const seededRef = useRef(false);

  // A different video's history should never seed onto a stale
  // transcript, in the unlikely case this hook's own instance
  // outlives a videoId change rather than remounting with the page.
  useEffect(() => {
    seededRef.current = false;
    setMessages([]);
  }, [videoId]);

  useEffect(() => {
    if (seededRef.current || !history.data) return;
    seededRef.current = true;
    setMessages(history.data.flatMap(toMessages));
  }, [history.data]);

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

  return { messages, send, clear, isSending, isHistoryLoading: history.isLoading };
}
