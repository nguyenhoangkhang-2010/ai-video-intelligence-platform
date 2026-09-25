import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ReactElement } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { SearchPanel } from "@/components/workspace/panels/SearchPanel";
import * as searchService from "@/services/search";

/** Same regression concern as ChatPanel.test.tsx: this panel's own
 * input must never be the thing blocking search, independent of
 * whatever gated the whole workspace before that bug was fixed. */
vi.mock("@/services/search");

function renderWithQueryClient(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NovaAttentionProvider>{ui}</NovaAttentionProvider>
    </QueryClientProvider>,
  );
}

describe("SearchPanel", () => {
  beforeEach(() => {
    vi.mocked(searchService.searchVideo).mockReset();
  });

  it("renders a focusable, typeable search input with no disabled attribute", () => {
    renderWithQueryClient(<SearchPanel videoId={1} />);

    const input = screen.getByPlaceholderText(/ask what this video covers/i);
    expect(input).toBeEnabled();
    expect(input).not.toHaveAttribute("disabled");
  });

  it("shows the idle empty state before any search has been run", () => {
    renderWithQueryClient(<SearchPanel videoId={1} />);
    expect(screen.getByText(/search within this video/i)).toBeInTheDocument();
  });

  it("lets the user type a query and submit it, then renders real results", async () => {
    const user = userEvent.setup();
    vi.mocked(searchService.searchVideo).mockResolvedValue({
      video_id: 1,
      query: "deployment strategy",
      results: [
        { vector_id: "v1", video_id: 1, chunk_index: 3, chunk_text: "We rolled out via blue-green deployment.", distance: 0.21 },
      ],
    });

    renderWithQueryClient(<SearchPanel videoId={1} />);

    const input = screen.getByPlaceholderText(/ask what this video covers/i);
    await user.type(input, "deployment strategy");
    await user.click(screen.getByRole("button", { name: /run search/i }));

    expect(searchService.searchVideo).toHaveBeenCalledWith(1, "deployment strategy");
    await waitFor(() => {
      expect(screen.getByText(/blue-green deployment/i)).toBeInTheDocument();
    });
    // The real chunk index is shown; no fabricated similarity score
    // anywhere in the rendered result.
    expect(screen.getByText(/segment 4/i)).toBeInTheDocument();
    expect(screen.queryByText(/%/)).not.toBeInTheDocument();
  });

  it("shows a clear button only once there is text, and clearing empties the input", async () => {
    const user = userEvent.setup();
    renderWithQueryClient(<SearchPanel videoId={1} />);

    expect(screen.queryByRole("button", { name: /clear search/i })).not.toBeInTheDocument();

    const input = screen.getByPlaceholderText(/ask what this video covers/i);
    await user.type(input, "test");
    const clearButton = screen.getByRole("button", { name: /clear search/i });

    await user.click(clearButton);
    expect(input).toHaveValue("");
  });

  it("renders a real no-results state, not a fabricated result", async () => {
    const user = userEvent.setup();
    vi.mocked(searchService.searchVideo).mockResolvedValue({
      video_id: 1,
      query: "something obscure",
      results: [],
    });

    renderWithQueryClient(<SearchPanel videoId={1} />);
    await user.type(screen.getByPlaceholderText(/ask what this video covers/i), "something obscure");
    await user.click(screen.getByRole("button", { name: /run search/i }));

    await waitFor(() => {
      expect(screen.getByText(/no matches found/i)).toBeInTheDocument();
    });
  });
});
