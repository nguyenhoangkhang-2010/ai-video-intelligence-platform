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
import { VideoDial } from "@/components/video/VideoDial";
import { VideoRow } from "@/components/video/VideoRow";
import { useDeleteVideo, useVideos } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { Video } from "@/types/video";

type SortKey = "recent" | "title" | "duration";
type ViewKey = "dials" | "list";

const SORT_OPTIONS: Array<{ key: SortKey; label: string }> = [
  { key: "recent", label: "Recent" },
  { key: "title", label: "Title" },
  { key: "duration", label: "Duration" },
];

const VIEW_OPTIONS: Array<{ key: ViewKey; label: string }> = [
  { key: "dials", label: "Dials" },
  { key: "list", label: "List" },
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

/** A row of framed toggle buttons - the case's pushers. */
function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: Array<{ key: T; label: string }>;
  value: T;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div role="group" aria-label={label} className="flex border border-text-primary/60">
      {options.map((option, index) => (
        <button
          key={option.key}
          type="button"
          onClick={() => onChange(option.key)}
          aria-pressed={value === option.key}
          className={cn(
            "index-label px-3 py-2 transition-colors duration-fast",
            index > 0 && "border-l border-text-primary/60",
            value === option.key ? "bg-text-primary text-surface" : "bg-surface-elevated text-text-secondary hover:text-text-primary",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/**
 * The library as a watch-winder case: the newest video sits on the
 * centre cushion as a large dial, the rest are smaller dials whose
 * reserve arc shows how long each runs relative to the longest one in
 * view. A list view stays one click away for scanning many at once.
 */
export default function LibraryPage() {
  const { data: videos, isLoading, isError, error, refetch } = useVideos();
  const deleteVideo = useDeleteVideo();

  const [pendingDelete, setPendingDelete] = useState<Video | null>(null);
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("recent");
  const [view, setView] = useState<ViewKey>("dials");

  const visibleVideos = useMemo(() => {
    if (!videos) return [];
    const filtered = query.trim()
      ? videos.filter((video) => video.title.toLowerCase().includes(query.trim().toLowerCase()))
      : videos;
    return sortVideos(filtered, sort);
  }, [videos, query, sort]);

  const longest = useMemo(() => Math.max(1, ...visibleVideos.map((video) => video.duration || 0)), [visibleVideos]);
  const totalSeconds = useMemo(() => (videos ?? []).reduce((sum, video) => sum + (video.duration || 0), 0), [videos]);

  const hasVideos = Boolean(videos && videos.length > 0);
  const isFiltering = hasVideos && query.trim().length > 0;
  // The "most recent" lead only makes sense in the default, unmodified
  // view - once the person is actively filtering/sorting, pinning a
  // featured item above their own query would be confusing.
  const showFeatured = hasVideos && !isFiltering && sort === "recent";
  const featured = showFeatured ? visibleVideos[0] : undefined;
  const restVideos = featured ? visibleVideos.slice(1) : visibleVideos;
  const indexOffset = featured ? 2 : 1;

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader
        eyebrow="Library · winder case"
        title="Your videos"
        description="Every upload becomes a searchable, explainable body of knowledge — transcript, summary, chapters and grounded Q&A."
        meta={
          hasVideos && (
            <dl className="hidden items-end gap-6 sm:flex">
              <div className="text-right">
                <dt className="index-label text-text-muted">Pieces</dt>
                <dd className="font-mono text-heading font-medium text-text-primary">{videos!.length}</dd>
              </div>
              <div className="text-right">
                <dt className="index-label text-text-muted">Total reserve</dt>
                <dd className="font-mono text-heading font-medium text-text-primary">
                  {Math.floor(totalSeconds / 3600)}h {String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0")}m
                </dd>
              </div>
            </dl>
          )
        }
        actions={
          <Link
            href={ROUTES.upload}
            className="inline-flex h-10 items-center gap-2 bg-lume px-4 text-body-sm font-semibold text-lume-on shadow-step-ink transition-[transform,box-shadow,background-color] duration-fast hover:bg-lume-hover active:translate-y-[3px] active:shadow-none"
          >
            <Icon name="upload" size={15} />
            Upload video
          </Link>
        }
      />

      {hasVideos && (
        <div className="flex shrink-0 flex-wrap items-center justify-between gap-3 px-6 py-4 sm:px-10">
          <div className="relative w-full max-w-xs">
            <Icon
              name="search"
              size={14}
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary"
            />
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Filter by title…"
              aria-label="Filter videos by title"
              className="h-9 w-full border border-text-primary/60 bg-surface-elevated pl-8 pr-2 text-body-sm text-text-primary placeholder:text-text-muted focus-visible:outline-2 focus-visible:outline-accent"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Segmented label="Sort videos" options={SORT_OPTIONS} value={sort} onChange={setSort} />
            <Segmented label="Library view" options={VIEW_OPTIONS} value={view} onChange={setView} />
          </div>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 pb-10 sm:px-10">
        {isLoading && (
          <div className="grid grid-cols-2 gap-8 pt-6 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="flex flex-col items-center gap-3">
                <Skeleton className="aspect-square w-full max-w-[200px] rounded-full" />
                <Skeleton className="h-3 w-2/3" />
              </div>
            ))}
          </div>
        )}

        {isError && <ErrorState error={toApiError(error)} onRetry={() => refetch()} />}

        {!isLoading && !isError && videos && videos.length === 0 && (
          <EmptyState
            icon="video"
            title="The case is empty"
            description="Upload your first video to get a transcript, summary and searchable chapters."
            action={
              <Link
                href={ROUTES.upload}
                className="mt-2 inline-flex h-9 items-center gap-1.5 bg-lume px-4 text-body-sm font-semibold text-lume-on shadow-step-ink"
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
                className="mt-2 border border-text-primary/60 px-3 py-1.5 text-body-sm font-medium text-text-primary transition-colors duration-fast hover:bg-surface"
              >
                Clear filter
              </button>
            }
          />
        )}

        {!isLoading && !isError && visibleVideos.length > 0 && (
          <div className="flex animate-fade-in flex-col gap-10">
            {featured && <FeaturedVideo video={featured} />}

            {restVideos.length > 0 && (
              <section>
                {featured && <p className="index-label mb-6 text-text-secondary">Rest of the case</p>}
                {view === "dials" ? (
                  <div className="grid grid-cols-2 gap-x-6 gap-y-12 sm:grid-cols-3 lg:grid-cols-4 2xl:grid-cols-5">
                    {restVideos.map((video, index) => (
                      <VideoDial
                        key={video.id}
                        video={video}
                        index={index + indexOffset}
                        reserve={(video.duration || 0) / longest}
                        onDelete={setPendingDelete}
                      />
                    ))}
                  </div>
                ) : (
                  <div className="flex flex-col border-t-2 border-text-primary">
                    {restVideos.map((video, index) => (
                      <VideoRow key={video.id} video={video} index={index + indexOffset} onDelete={setPendingDelete} />
                    ))}
                  </div>
                )}
              </section>
            )}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete this video?"
        description={
          pendingDelete
            ? `"${pendingDelete.title}" and everything generated from it — transcript, summary, chapters, quizzes, flashcards — will be permanently removed.`
            : undefined
        }
        error={deleteVideo.isError ? toApiError(deleteVideo.error).message : null}
        confirmLabel={deleteVideo.isError ? "Try again" : "Delete video"}
        danger
        isConfirming={deleteVideo.isPending}
        onCancel={() => {
          setPendingDelete(null);
          deleteVideo.reset();
        }}
        onConfirm={() => {
          if (!pendingDelete) return;
          // Only closes on success — a failed delete keeps the dialog
          // open with the real error shown above, so the person can
          // retry or cancel instead of silently losing the attempt
          // (previously this closed via onSettled regardless of
          // outcome, so a failure was never visible anywhere).
          deleteVideo.mutate(pendingDelete.id, {
            onSuccess: () => setPendingDelete(null),
          });
        }}
      />
    </div>
  );
}
