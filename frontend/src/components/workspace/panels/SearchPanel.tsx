"use client";

import { useEffect, useState, type FormEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Highlight } from "@/components/ui/Highlight";
import { Icon } from "@/components/ui/Icon";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useVideoSearch } from "@/hooks/useSearch";
import { toApiError } from "@/lib/axios";

/**
 * Video-scoped semantic search, presented as a direct line into the
 * video's intelligence layer — a command input, not a boxed search
 * form — with results as a flowing stream rather than a stack of
 * bordered cards. Results show real chunk text and chunk_index only —
 * no timestamp (the API doesn't return one) and no fabricated
 * similarity percentage from the raw FAISS distance (see
 * types/search.ts) — results are only ever presented in the backend's
 * own relevance order (#1 = closest match), never as an invented score.
 */
export function SearchPanel({ videoId }: { videoId: number }) {
  const [query, setQuery] = useState("");
  const search = useVideoSearch(videoId);
  const { notice } = useNovaAttention();

  // The shared Nova entity reflects the real retrieval lifecycle -
  // querying the video's intelligence layer is genuinely "searching",
  // not a decorative loop independent of the actual request.
  useEffect(() => {
    if (search.isPending) notice("searching");
    else if (search.isSuccess) notice("success", 1200);
  }, [search.isPending, search.isSuccess, notice]);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (query.trim()) search.mutate(query.trim());
  }

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="search"
        label="Query the intelligence layer"
        tone="ai"
        meta={search.isSuccess && <span>{search.data.results.length} result{search.data.results.length === 1 ? "" : "s"}</span>}
      />

      <form onSubmit={handleSubmit} className="flex shrink-0 items-center gap-2.5 border-b border-border px-5 py-6 sm:px-6">
        <div className="mx-auto flex w-full max-w-2xl items-center gap-3">
          <span className="font-mono text-display text-ai" aria-hidden="true">
            ›
          </span>
          <input
            type="text"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Ask what this video covers…"
            aria-label="Search this video's content"
            className="h-10 flex-1 bg-transparent text-heading-sm text-text-primary placeholder:text-text-muted focus-visible:outline-none"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-text-muted transition-colors duration-fast hover:bg-surface-elevated hover:text-text-secondary"
            >
              <Icon name="close" size={13} />
            </button>
          )}
          <button
            type="submit"
            disabled={!query.trim() || search.isPending}
            aria-label="Run search"
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ai-muted text-ai transition-colors duration-fast hover:bg-ai/25 disabled:opacity-40"
          >
            <Icon
              name={search.isPending ? "spinner" : "chevron-right"}
              size={15}
              className={search.isPending ? "animate-spin" : undefined}
            />
          </button>
        </div>
      </form>

      <div className="flex-1 overflow-y-auto">
        {search.status === "idle" && (
          <EmptyState
            icon="search"
            title="Search within this video"
            description="Semantic retrieval finds the moments that mean what you're asking, not just literal keyword matches."
          />
        )}

        {search.isPending && (
          <div className="flex flex-col gap-4 px-5 py-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-4 w-full" />
            ))}
          </div>
        )}

        {search.isError && (
          <ErrorState error={toApiError(search.error)} onRetry={() => search.mutate(query)} compact className="p-4" />
        )}

        {search.isSuccess && search.data.results.length === 0 && (
          <EmptyState
            icon="search"
            title="No matches found"
            description={`Nothing in this video's transcript closely matches "${search.data.query}".`}
          />
        )}

        {search.isSuccess && search.data.results.length > 0 && (
          <ol className="mx-auto flex max-w-2xl flex-col divide-y divide-border">
            {search.data.results.map((result, index) => (
              <li
                key={result.vector_id}
                className="group flex animate-mode-enter gap-4 border-l-2 border-transparent px-5 py-4 transition-colors duration-fast hover:border-ai hover:bg-surface-hover sm:px-1"
                style={{ animationDelay: `${Math.min(index, 6) * 45}ms` }}
              >
                <span className="mt-0.5 shrink-0 font-mono text-caption text-ai">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="mb-1 text-caption text-text-disabled">Segment {result.chunk_index + 1}</p>
                  <p className="text-body-sm leading-relaxed text-text-secondary">
                    <Highlight text={result.chunk_text} query={search.data.query} />
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
