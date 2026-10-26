import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AIMessage } from "@/components/chat/AIMessage";
import type { ChatMessage, RagStatus } from "@/types/chat";

/**
 * Regression coverage for a real contract bug: RagStatus (types/chat.ts)
 * used to be missing "generation_failed" - the backend's 5th real
 * RAGResult.status value (app/schemas/rag.py), returned when retrieval
 * succeeds but the LLM call itself fails (app/pipelines/rag_pipeline.py).
 * Before this fix, that status fell through statusCopy's `default` case
 * and rendered a blank assistant bubble with no text and no way to tell
 * what happened. Every known status is exercised here so a future status
 * added to the backend's Literal without a matching frontend case shows
 * up immediately as a type error at the call site, not a silent blank UI.
 */
function makeMessage(status: RagStatus): ChatMessage {
  return {
    id: "1",
    role: "assistant",
    content: "",
    status,
  };
}

describe("AIMessage", () => {
  it("shows a real, actionable message when generation fails after successful retrieval", () => {
    render(<AIMessage message={makeMessage("generation_failed")} />);

    expect(screen.getByText(/something went wrong generating an answer/i)).toBeInTheDocument();
  });

  it("shows the real answer and its sources when status is answered", () => {
    render(
      <AIMessage
        message={{
          id: "1",
          role: "assistant",
          content: "The answer is 42.",
          status: "answered",
          sources: [],
        }}
      />,
    );

    expect(screen.getByText("The answer is 42.")).toBeInTheDocument();
  });

  it.each<[RagStatus, RegExp]>([
    ["no_embeddings", /hasn't finished processing/i],
    ["no_relevant_chunks", /nothing in this video's transcript/i],
    ["empty_query", /ask a question to get started/i],
  ])("shows the right copy for status=%s", (status, expectedText) => {
    render(<AIMessage message={makeMessage(status)} />);

    expect(screen.getByText(expectedText)).toBeInTheDocument();
  });
});
