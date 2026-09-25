import { AxiosError } from "axios";
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
  return render(
    <NovaAttentionProvider>
      <ChatPanel {...props} />
    </NovaAttentionProvider>,
  );
}

describe("ChatPanel", () => {
  beforeEach(() => {
    vi.mocked(chatService.askVideo).mockReset();
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
});
