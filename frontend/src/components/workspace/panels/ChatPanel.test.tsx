import { AxiosError } from "axios";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { ChatPanel } from "@/components/workspace/panels/ChatPanel";
import * as chatService from "@/services/chat";

/**
 * Regression coverage for the workspace-wide input-lock bug: a
 * top-level `video.status === "processed"` gate in
 * app/(app)/videos/[id]/page.tsx used to replace this entire panel
 * (and every other non-Overview tab) with a static notice whenever a
 * video hadn't finished processing - meaning the textarea below was
 * simply never rendered, regardless of anything in this component
 * itself. That gate has been removed; these tests exercise ChatPanel
 * in isolation to lock in that its own input is never disabled for
 * any reason other than an in-flight request.
 */
vi.mock("@/services/chat");

/**
 * ChatPanel no longer owns a 3D Nova instance - it reads/drives the
 * single, page-wide Nova entity through NovaAttentionContext (see
 * NovaAmbient, mounted once at the app root, not under test here).
 * A real provider is enough; nothing 3D/WebGL needs mocking anymore.
 */
function renderChatPanel(props: Parameters<typeof ChatPanel>[0]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NovaAttentionProvider>
        <ChatPanel {...props} />
      </NovaAttentionProvider>
    </QueryClientProvider>,
  );
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.mocked(chatService.askVideo).mockReset();
    // These tests cover the regular request path: the stream reports
    // "unavailable" (as it does when it can't be opened), so useChat
    // falls back to askVideo. Streaming has its own tests below.
    vi.mocked(chatService.askVideoStream)
      .mockReset()
      .mockRejectedValue(Object.assign(new Error("unavailable"), { code: "STREAM_UNAVAILABLE" }));
    // useChat seeds from persisted history on mount (see
    // hooks/useChat.ts) - an empty history is the real "no prior
    // turns yet" case these tests exercise, not an unmocked gap.
    vi.mocked(chatService.getChatHistory).mockReset().mockResolvedValue([]);
  });

  it("renders a focusable, typeable message input with no disabled attribute", () => {
    renderChatPanel({ videoId: 1 });

    const input = screen.getByPlaceholderText(/ask a question about this video/i);
    expect(input).toBeEnabled();
    expect(input).not.toHaveAttribute("disabled");
  });

  it("lets the user type a message and submit it by pressing Enter", async () => {
    const user = userEvent.setup();
    vi.mocked(chatService.askVideo).mockResolvedValue({
      video_id: 1,
      query: "What is this video about?",
      status: "answered",
      answer: "It covers the deployment process.",
      sources: [],
    });

    renderChatPanel({ videoId: 1 });

    const input = screen.getByPlaceholderText(/ask a question about this video/i);
    await user.click(input);
    await user.type(input, "What is this video about?");
    await user.keyboard("{Enter}");

    expect(chatService.askVideo).toHaveBeenCalledWith(1, "What is this video about?");
    await waitFor(() => {
      expect(screen.getByText("It covers the deployment process.")).toBeInTheDocument();
    });

    // The input is cleared and ready for the next question - not
    // stuck disabled after a successful send.
    await waitFor(() => expect(input).toHaveValue(""));
    expect(input).toBeEnabled();
  });

  it("inserts a newline on Shift+Enter instead of submitting", async () => {
    const user = userEvent.setup();
    renderChatPanel({ videoId: 1 });

    const input = screen.getByPlaceholderText(/ask a question about this video/i);
    await user.click(input);
    await user.keyboard("line one{Shift>}{Enter}{/Shift}line two");

    expect(input).toHaveValue("line one\nline two");
    expect(chatService.askVideo).not.toHaveBeenCalled();
  });

  it("disables the send button only while empty or while a request is in flight", async () => {
    const user = userEvent.setup();
    let resolveAsk: (value: Awaited<ReturnType<typeof chatService.askVideo>>) => void = () => {};
    vi.mocked(chatService.askVideo).mockReturnValue(
      new Promise((resolve) => {
        resolveAsk = resolve;
      }),
    );

    renderChatPanel({ videoId: 1 });
    const input = screen.getByPlaceholderText(/ask a question about this video/i);
    const sendButton = screen.getByRole("button", { name: /send message/i });

    expect(sendButton).toBeDisabled(); // empty draft

    await user.type(input, "hello");
    expect(sendButton).toBeEnabled();

    await user.click(sendButton);
    expect(sendButton).toBeDisabled(); // in-flight request

    resolveAsk({ video_id: 1, query: "hello", status: "answered", answer: "hi", sources: [] });
    await waitFor(() => expect(sendButton).toBeDisabled()); // empty again after send clears the draft
  });

  it("shows a real error state instead of a silent failure when the API call rejects", async () => {
    const user = userEvent.setup();
    // A real network failure, as axios itself throws it: an AxiosError
    // with no `.response` (as opposed to a plain Error, which
    // toApiError treats as an unrecognized/unexpected error instead).
    vi.mocked(chatService.askVideo).mockRejectedValue(new AxiosError("Network Error"));

    renderChatPanel({ videoId: 1 });
    const input = screen.getByPlaceholderText(/ask a question about this video/i);
    await user.type(input, "hello{Enter}");

    await waitFor(() => {
      expect(screen.getByText(/can't reach the server/i)).toBeInTheDocument();
    });
  });

  describe("streaming answers", () => {
    it("shows the answer word by word as it streams, without the regular request", async () => {
      const user = userEvent.setup();
      let finish: () => void = () => {};
      vi.mocked(chatService.askVideoStream).mockImplementation(async (_videoId, query, handlers) => {
        handlers.onSources?.([]);
        handlers.onToken("Lạm phát ");
        handlers.onToken("là mức tăng");
        await new Promise<void>((resolve) => {
          finish = resolve;
        });
        handlers.onToken(" giá cả.");
        return { video_id: 1, query, status: "answered", answer: "Lạm phát là mức tăng giá cả.", sources: [] };
      });

      renderChatPanel({ videoId: 1 });
      await user.type(screen.getByPlaceholderText(/ask a question about this video/i), "Lạm phát là gì?{Enter}");

      // Partial answer is visible while the model is still writing.
      expect(await screen.findByText(/Lạm phát là mức tăng/)).toBeInTheDocument();
      expect(screen.queryByText(/analyzing the transcript/i)).not.toBeInTheDocument();

      finish();
      await waitFor(() => {
        expect(screen.getByText("Lạm phát là mức tăng giá cả.")).toBeInTheDocument();
      });
      expect(chatService.askVideo).not.toHaveBeenCalled();
      expect(chatService.askVideoStream).toHaveBeenCalledWith(1, "Lạm phát là gì?", expect.any(Object));
    });

    it("drops partial text and shows the failure state when generation fails mid-answer", async () => {
      const user = userEvent.setup();
      vi.mocked(chatService.askVideoStream).mockImplementation(async (_videoId, query, handlers) => {
        handlers.onToken("Một nửa câu trả");
        return { video_id: 1, query, status: "generation_failed", answer: null, sources: [] };
      });

      renderChatPanel({ videoId: 1 });
      await user.type(screen.getByPlaceholderText(/ask a question about this video/i), "hello{Enter}");

      await waitFor(() => {
        expect(screen.getByText(/something went wrong generating an answer/i)).toBeInTheDocument();
      });
      expect(screen.queryByText("Một nửa câu trả")).not.toBeInTheDocument();
      expect(chatService.askVideo).not.toHaveBeenCalled();
    });

    it("reports a stream that breaks off mid-answer instead of silently retrying", async () => {
      const user = userEvent.setup();
      vi.mocked(chatService.askVideoStream).mockImplementation(async (_videoId, _query, handlers) => {
        handlers.onToken("partial");
        throw new Error("The answer was cut off before it finished. Please try again.");
      });

      renderChatPanel({ videoId: 1 });
      await user.type(screen.getByPlaceholderText(/ask a question about this video/i), "hello{Enter}");

      await waitFor(() => {
        expect(screen.getByText(/answer was cut off/i)).toBeInTheDocument();
      });
      expect(chatService.askVideo).not.toHaveBeenCalled();
    });
  });
});
