"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";

import { Nova } from "@/components/3d/Nova";
import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton, Spinner } from "@/components/ui/Spinner";
import { ChapterStrip } from "@/components/workspace/ChapterStrip";
import { ChronographDial, type SubDialDef } from "@/components/workspace/ChronographDial";
import { ModeTabs } from "@/components/workspace/ModeTabs";
import { ProcessingBanner } from "@/components/workspace/ProcessingBanner";
import { WorkspaceHeader } from "@/components/workspace/WorkspaceHeader";
import {
  WORKSPACE_SECTION_GROUPS,
  WORKSPACE_SECTIONS,
  type WorkspaceSection,
} from "@/components/workspace/sections";
import { ChatPanel } from "@/components/workspace/panels/ChatPanel";
import { ChaptersPanel } from "@/components/workspace/panels/ChaptersPanel";
import { FlashcardsPanel } from "@/components/workspace/panels/FlashcardsPanel";
import { OverviewPanel } from "@/components/workspace/panels/OverviewPanel";
import { QuizPanel } from "@/components/workspace/panels/QuizPanel";
import { SearchPanel } from "@/components/workspace/panels/SearchPanel";
import { SummaryPanel } from "@/components/workspace/panels/SummaryPanel";
import { TranscriptPanel } from "@/components/workspace/panels/TranscriptPanel";
import { TranslationPanel } from "@/components/workspace/panels/TranslationPanel";
import { VideoPlayer } from "@/components/video/VideoPlayer";
import { VideoPlayerProvider } from "@/hooks/useVideoPlayer";
import { useChapters } from "@/hooks/useChapters";
import { useMediaToken, useVideo } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import { cn } from "@/lib/utils";
import { getVideoStreamUrl } from "@/services/videos";

const SUB_DIALS: SubDialDef[] = [
  { label: "Watch", icon: "video", tone: "ink" },
  { label: "Understand", icon: "summary", tone: "lume" },
  { label: "Ask", icon: "chat", tone: "ai" },
  { label: "Study", icon: "quiz", tone: "atmosphere" },
];

/**
 * The workspace as a chronograph: on the left the case, with the real
 * video set into the dial and the bezel as its timeline; four
 * sub-dials pick a group (Watch / Understand / Ask / Study) and the
 * crown steps through all nine modes in order. On the right, the
 * active mode's panel with that group's modes as engraved tabs. Nova
 * sits in a porthole at the panel's corner, driven by the shared
 * NovaAttentionContext (Chat/Search tell it what's happening).
 */
export default function VideoWorkspacePage() {
  const params = useParams<{ id: string }>();
  const videoId = Number(params.id);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("overview");
  const { state: novaState, notice } = useNovaAttention();
  // Quiz/Flashcards own real session progress (which questions were
  // answered, which cards were flipped) in local component state -
  // every other panel remounts on tab switch (see the key={activeSection}
  // below) with no such state to lose. Once a person has opened one of
  // these two, it stays mounted (hidden via CSS, not unmounted) for the
  // rest of this page visit so that progress survives switching away
  // and back - never persisted beyond this visit, and never affecting
  // any other panel's existing remount-on-switch behavior.
  const [keepAliveSections, setKeepAliveSections] = useState<ReadonlySet<WorkspaceSection>>(
    () => new Set(),
  );

  function handleSelectSection(section: WorkspaceSection) {
    setActiveSection(section);
    if (WORKSPACE_SECTIONS.find((candidate) => candidate.id === section)?.tone === "ai") notice("attention", 900);
    if (section === "quiz" || section === "flashcards") {
      setKeepAliveSections((current) => (current.has(section) ? current : new Set(current).add(section)));
    }
  }

  const video = useVideo(videoId);
  const chapters = useChapters(videoId, video.data?.status);
  const mediaToken = useMediaToken(videoId);
  const streamUrl = useMemo(
    () => (mediaToken.data ? getVideoStreamUrl(videoId, mediaToken.data) : null),
    [videoId, mediaToken.data],
  );

  if (video.isLoading) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 p-6">
        <Spinner size={40} className="text-text-primary" />
        <p className="index-label text-text-secondary">Winding the movement…</p>
      </div>
    );
  }

  if (video.isError || !video.data) {
    return (
      <div className="flex h-full items-center justify-center">
        <ErrorState error={toApiError(video.error)} onRetry={() => video.refetch()} />
      </div>
    );
  }

  const chapterList = chapters.data ?? [];
  const activeGroup =
    WORKSPACE_SECTION_GROUPS.find((group) => group.ids.includes(activeSection)) ?? WORKSPACE_SECTION_GROUPS[0]!;
  const order = WORKSPACE_SECTIONS.map((section) => section.id);

  function handleCrown(direction: 1 | -1) {
    const index = order.indexOf(activeSection);
    const next = order[(index + direction + order.length) % order.length];
    if (next) handleSelectSection(next);
  }

  function handleSelectGroup(label: string) {
    const group = WORKSPACE_SECTION_GROUPS.find((candidate) => candidate.label === label);
    if (!group || group.label === activeGroup.label) return;
    handleSelectSection(group.ids[0]!);
  }

  return (
    <VideoPlayerProvider>
      <div className="flex h-full flex-col overflow-y-auto lg:overflow-hidden">
        <WorkspaceHeader video={video.data} />
        <ProcessingBanner video={video.data} />

        <div className="flex min-h-0 flex-1 flex-col lg:flex-row">
          {/* The case - dial, bezel timeline, sub-dials, crown. */}
          <section
            aria-label="Video dial"
            className="flex min-w-0 shrink-0 flex-col items-center px-4 py-4 sm:px-8 lg:basis-[54%] lg:overflow-y-auto"
          >
            {/*
             * Fits the viewport height when it can, but never shrinks
             * below 560px - a fully height-capped dial collapsed to a tiny
             * video on short laptop screens. Below that the column scrolls
             * instead, and `my-auto` keeps it centred when there is room
             * without clipping its top when there isn't.
             */}
            <div className="my-auto flex w-full flex-col items-center gap-4">
              <div className="w-full pr-[4%]" style={{ maxWidth: "min(100%, 780px, max(560px, 100vh - 150px))" }}>
                <ChronographDial
                  chapters={chapterList}
                  fallbackDuration={video.data.duration}
                  subDials={SUB_DIALS}
                  activeSubDial={activeGroup.label}
                  onSelectSubDial={handleSelectGroup}
                  onCrown={handleCrown}
                >
                  {streamUrl ? (
                    <VideoPlayer
                      src={streamUrl}
                      title={video.data.title}
                      chapters={chapterList}
                      fallbackDuration={video.data.duration}
                      fill
                    />
                  ) : mediaToken.isError ? (
                    <div className="flex h-full w-full items-center justify-center bg-surface">
                      <ErrorState error={toApiError(mediaToken.error)} onRetry={() => mediaToken.refetch()} compact />
                    </div>
                  ) : (
                    <Skeleton className="h-full w-full" />
                  )}
                </ChronographDial>
              </div>
              {chapterList.length > 0 && (
                <div className="w-full max-w-xl">
                  <ChapterStrip chapters={chapterList} />
                </div>
              )}
            </div>
          </section>

          {/* The active mode's panel. */}
          <section
            aria-label="Workspace panel"
            className="relative flex min-h-[70vh] min-w-0 flex-1 flex-col border-t-2 border-text-primary bg-surface lg:min-h-0 lg:border-l-2 lg:border-t-0"
          >
            <nav
              aria-label="Workspace modes"
              className="shrink-0 border-b border-text-primary/25 pr-20"
            >
              <ModeTabs active={activeSection} onSelect={handleSelectSection} />
            </nav>

            {/*
             * Nova's porthole - positioned on its own wrapper outside the
             * scrolling panel (NovaImpl's root is always `relative`, so
             * positioning must live on a parent, not on <Nova> itself).
             */}
            <div className="pointer-events-none absolute right-3 top-1.5 z-30 h-14 w-14 rounded-full border-[3px] border-case bg-surface-sunken">
              <Nova state={novaState} mode="workspace" className="h-full w-full" />
            </div>

            <div className="relative min-h-0 flex-1 overflow-y-auto">
              <div className="mx-auto h-full w-full max-w-5xl">
                {activeSection !== "quiz" && activeSection !== "flashcards" && (
                  <div key={activeSection} className="h-full animate-mode-enter">
                    <ActivePanel
                      section={activeSection}
                      videoId={videoId}
                      onNavigate={handleSelectSection}
                      video={video.data}
                    />
                  </div>
                )}
                {/*
                 * Quiz/Flashcards stay mounted (hidden via CSS, not
                 * unmounted/remounted) once first visited - see the
                 * keepAliveSections comment near the top of this
                 * component: their session progress lives in local
                 * component state a remount would silently reset.
                 */}
                {keepAliveSections.has("quiz") && (
                  <div className={cn("h-full", activeSection === "quiz" ? "animate-mode-enter" : "hidden")}>
                    <QuizPanel videoId={videoId} videoStatus={video.data.status} />
                  </div>
                )}
                {keepAliveSections.has("flashcards") && (
                  <div className={cn("h-full", activeSection === "flashcards" ? "animate-mode-enter" : "hidden")}>
                    <FlashcardsPanel videoId={videoId} videoStatus={video.data.status} />
                  </div>
                )}
              </div>
            </div>
          </section>
        </div>
      </div>
    </VideoPlayerProvider>
  );
}

function ActivePanel({
  section,
  videoId,
  onNavigate,
  video,
}: {
  section: WorkspaceSection;
  videoId: number;
  onNavigate: (section: WorkspaceSection) => void;
  video: NonNullable<ReturnType<typeof useVideo>["data"]>;
}) {
  switch (section) {
    case "overview":
      return <OverviewPanel video={video} onNavigate={onNavigate} />;
    case "transcript":
      return <TranscriptPanel videoId={videoId} videoStatus={video.status} />;
    case "summary":
      return <SummaryPanel videoId={videoId} videoStatus={video.status} />;
    case "translation":
      return <TranslationPanel videoId={videoId} videoStatus={video.status} />;
    case "search":
      return <SearchPanel videoId={videoId} />;
    case "chat":
      return <ChatPanel videoId={videoId} videoTitle={video.title} />;
    case "chapters":
      return <ChaptersPanel videoId={videoId} videoStatus={video.status} />;
    // "quiz"/"flashcards" are rendered outside ActivePanel - see the
    // keepAliveSections blocks in VideoWorkspacePage above.
    default:
      return null;
  }
}
