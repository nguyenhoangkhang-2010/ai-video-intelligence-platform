"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { Skeleton } from "@/components/ui/Spinner";
import { FeaturedVideo } from "@/components/video/FeaturedVideo";
import { VideoRow } from "@/components/video/VideoRow";
import { useDeleteVideo, useVideos } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Video } from "@/types/video";

type SortKey = "recent" | "title" | "duration";

const SORT_OPTIONS: Array<{ key: SortKey; label: string }> = [
  { key: "recent", label: "Recent" },
  { key: "title", label: "Title" },
  { key: "duration", label: "Duration" },
];

function sortVideos(videos: Video[], sort: SortKey): Video[] {
  const copy = [...videos];
  switch (sort) {
    case "title":
      return copy.sort((a, b) => a.title.localeCompare(b.title));
    case "duration":
      return copy.sort((a, b) => b.duration - a.duration);
    case "recent":
    default:
      return copy.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
  }
}

export default function LibraryPage() {
  const { data: videos, isLoading, isError, error, refetch } = useVideos();
  const deleteVideo = useDeleteVideo();

  const [pendingDelete, setPendingDelete] = useState<Video | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("recent");

  const visibleVideos = useMemo(() => {
    if (!videos) return [];
    const filtered = query.trim()
      ? videos.filter((video) => video.title.toLowerCase().includes(query.trim().toLowerCase()))
      : videos;
    return sortVideos(filtered, sort);
  }, [videos, query, sort]);

  const hasVideos = Boolean(videos && videos.length > 0);
  const isFiltering = hasVideos && query.trim().length > 0;
  // The editorial "most recent" lead only makes sense in the default,
  // unmodified view - once the person is actively filtering/sorting,
  // pinning a featured item above their own query would be confusing.
  const showFeatured = hasVideos && !isFiltering && sort === "recent";
  const featured = showFeatured ? visibleVideos[0] : undefined;
  const gridVideos = featured ? visibleVideos.slice(1) : visibleVideos;

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <div
        className="pointer-events-none absolute -top-32 right-[-10%] z-0 h-[480px] w-[480px] rounded-full bg-[radial-gradient(ellipse_at_center,rgb(var(--color-accent)/0.1),transparent_70%)]"
        aria-hidden="true"
      />

      <div className="relative z-10 flex h-full flex-col overflow-hidden">
        <PageHeader
          eyebrow="Library"
          title="Your videos"
          description="Every upload here becomes a searchable, explainable body of knowledge — transcript, summary, chapters, and grounded Q&A."
          meta={
            hasVideos && (
              <span className="hidden font-mono text-body-sm text-text-muted sm:inline">
                {videos!.length} video{videos!.length === 1 ? "" : "s"}
              </span>
            )
          }
          actions={
            <Link
              href={ROUTES.upload}
              className="inline-flex h-9 items-center gap-2 rounded bg-accent px-4 text-body font-medium text-accent-on transition-colors duration-fast hover:bg-accent-hover"
            >
              <Icon name="upload" size={15} />
              Upload video
            </Link>
          }
        />

        {hasVideos && (
          <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-b border-border px-6 py-3 sm:px-8">
            <div className="relative w-full max-w-xs">
              <Icon
                name="search"
                size={14}
                className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-text-muted"
              />
              <input
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Filter by title…"
                aria-label="Filter videos by title"
                className="h-8 w-full rounded border border-border-strong bg-surface-sunken pl-7 pr-2 text-body-sm text-text-primary placeholder:text-text-muted transition-colors duration-fast focus-visible:outline-2 focus-visible:outline-accent"
              />
            </div>

            <div className="flex items-center gap-1 rounded-md border border-border-strong bg-surface-sunken p-0.5">
              {SORT_OPTIONS.map((option) => (
                <button
                  key={option.key}
                  type="button"
                  onClick={() => setSort(option.key)}
                  aria-pressed={sort === option.key}
                  className={cn(
                    "rounded px-2.5 py-1 text-caption font-medium transition-colors duration-fast",
                    sort === option.key
                      ? "bg-surface-elevated text-text-primary"
                      : "text-text-muted hover:text-text-secondary",
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-6 py-6 sm:px-8">
          {isLoading && (
            <div className="flex flex-col divide-y divide-border">
              {Array.from({ length: 6 }).map((_, index) => (
                <div key={index} className="flex items-center gap-5 py-3">
                  <Skeleton className="aspect-video w-36 shrink-0 rounded-md" />
                  <div className="flex flex-1 flex-col gap-2">
                    <Skeleton className="h-4 w-1/2" />
                    <Skeleton className="h-3 w-1/4" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && <ErrorState error={toApiError(error)} onRetry={() => refetch()} />}

          {!isLoading && !isError && videos && videos.length === 0 && (
            <EmptyState
              icon="video"
              title="No videos yet"
              description="Upload your first video to get a transcript, summary, and searchable chapters."
              action={
                <Link
                  href={ROUTES.upload}
                  className="mt-2 inline-flex h-8 items-center gap-1.5 rounded bg-accent px-3 text-body-sm font-medium text-accent-on transition-colors duration-fast hover:bg-accent-hover"
                >
                  <Icon name="upload" size={15} />
                  Upload video
                </Link>
              }
            />
          )}

          {!isLoading && !isError && isFiltering && visibleVideos.length === 0 && (
            <EmptyState
              icon="search"
              title="No matching videos"
              description={`Nothing in your library matches "${query.trim()}".`}
              action={
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  className="mt-2 rounded border border-border-strong px-3 py-1.5 text-body-sm font-medium text-text-secondary transition-colors duration-fast hover:border-accent hover:text-text-primary"
                >
                  Clear filter
                </button>
              }
            />
          )}

          {!isLoading && !isError && visibleVideos.length > 0 && (
            <div className="flex animate-fade-in flex-col gap-8">
              {featured && <FeaturedVideo video={featured} />}
              {gridVideos.length > 0 && (
                <div>
                  {featured && (
                    <p className="mb-1 text-label font-semibold uppercase tracking-wide text-text-secondary">
                      Rest of your library
                    </p>
                  )}
                  <div className="flex flex-col divide-y divide-border">
                    {gridVideos.map((video) => (
                      <VideoRow key={video.id} video={video} onDelete={setPendingDelete} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this video?"
        description={
          pendingDelete
            ? `"${pendingDelete.title}" and everything generated from it — transcript, summary, chapters, quizzes, flashcards — will be permanently removed.`
            : undefined
        }
        confirmLabel="Delete video"
        danger
        isConfirming={deleteVideo.isPending}
        onCancel={() => setPendingDelete(null)}
        onConfirm={() => {
          if (!pendingDelete) return;
          deleteVideo.mutate(pendingDelete.id, {
            onSettled: () => setPendingDelete(null),
          });
        }}
      />
    </div>
  );
}
