"use client";

import { useParams } from "next/navigation";
import { useMemo, useState, type UIEvent } from "react";

import { Nova } from "@/components/3d/Nova";
import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Spinner";
import { atmosphereGradient, SECTION_ATMOSPHERE } from "@/components/workspace/atmosphere";
import { ChapterStrip } from "@/components/workspace/ChapterStrip";
import { ProcessingBanner } from "@/components/workspace/ProcessingBanner";
import { WorkspaceHeader } from "@/components/workspace/WorkspaceHeader";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";
import type { WorkspaceSection } from "@/components/workspace/sections";
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
import { useVideo } from "@/hooks/useVideos";
import { toApiError } from "@/lib/axios";
import { getVideoStreamUrl } from "@/services/videos";

/**
 * The Intelligence Studio: a cinematic media stage up top (not a
 * bordered card), an always-visible mode bar, and an active
 * intelligence environment below it that carries its own subtle
 * per-mode atmosphere (see atmosphere.ts) - a real spatial
 * relationship between three layers, not "video + tabs + panel".
 * Nova lives inside this same canvas as a workspace-scale ambient
 * presence (see NovaScene's "workspace" mode), reacting to whatever
 * the shared NovaAttentionContext says is actually happening
 * (Chat/Search driving it, same as everywhere else) - not a second
 * canvas, not an avatar in the header.
 */
export default function VideoWorkspacePage() {
  const params = useParams<{ id: string }>();
  const videoId = Number(params.id);
  const [activeSection, setActiveSection] = useState<WorkspaceSection>("overview");
  const [navCompact, setNavCompact] = useState(false);
  const { state: novaState } = useNovaAttention();

  function handleContentScroll(event: UIEvent<HTMLDivElement>) {
    setNavCompact(event.currentTarget.scrollTop > 24);
  }

  // Each panel starts scrolled to its own top, so switching sections
  // always drops the nav back out of its compact state rather than
  // staying collapsed for a panel the person hasn't scrolled yet.
  function handleSelectSection(section: WorkspaceSection) {
    setActiveSection(section);
    setNavCompact(false);
  }

  const video = useVideo(videoId);
  const chapters = useChapters(videoId, video.data?.status);
  const streamUrl = useMemo(() => getVideoStreamUrl(videoId), [videoId]);

  if (video.isLoading) {
    return (
      <div className="flex h-full flex-col gap-4 p-6">
        <Skeleton className="h-14 w-full" />
        <Skeleton className="flex-1" />
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
  const atmosphere = atmosphereGradient(SECTION_ATMOSPHERE[activeSection]);

  return (
    <VideoPlayerProvider>
      <div className="flex h-full flex-col overflow-hidden">
        <WorkspaceHeader video={video.data} />
        <ProcessingBanner video={video.data} />

        <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
          {/* Cinematic media stage — atmosphere behind the frame, a soft vignette on it, not a bordered card. */}
          <div className="relative shrink-0 overflow-hidden border-b border-border bg-bg-secondary px-5 py-7 sm:px-8 sm:py-9">
            <div
              className="pointer-events-none absolute inset-0 opacity-70"
              style={{
                background:
                  "radial-gradient(ellipse 900px 500px at 50% -10%, rgb(var(--color-accent) / 0.1), transparent 60%)",
              }}
              aria-hidden="true"
            />
            <div className="relative mx-auto flex w-full max-w-5xl flex-col gap-3">
              <div className="overflow-hidden rounded-2xl shadow-lg ring-1 ring-black/[0.06]">
                <VideoPlayer src={streamUrl} title={video.data.title} chapters={chapterList} />
              </div>
              {chapterList.length > 0 && <ChapterStrip chapters={chapterList} />}
            </div>
          </div>

          <WorkspaceNav active={activeSection} onSelect={handleSelectSection} compact={navCompact} />

          <div className="relative min-h-0 flex-1 overflow-y-auto" onScroll={handleContentScroll}>
            {atmosphere && (
              <div
                className="pointer-events-none absolute inset-0 z-0 transition-[background] duration-slow"
                style={{ background: atmosphere }}
                aria-hidden="true"
              />
            )}

            {/* Nova's workspace presence — behind the content column, never covering it (z-0 vs. the panel's own z-10), hidden below lg where there's no room to spare. */}
            <Nova
              state={novaState}
              mode="workspace"
              className="pointer-events-none absolute bottom-0 right-0 z-0 hidden opacity-[0.55] lg:block lg:h-72 lg:w-72 xl:h-80 xl:w-80"
            />

            <div className="relative z-10 mx-auto h-full w-full max-w-5xl">
              <div key={activeSection} className="h-full animate-rise">
                <ActivePanel
                  section={activeSection}
                  videoId={videoId}
                  onNavigate={handleSelectSection}
                  video={video.data}
                />
              </div>
            </div>
          </div>
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
    case "quiz":
      return <QuizPanel videoId={videoId} videoStatus={video.status} />;
    case "chapters":
      return <ChaptersPanel videoId={videoId} videoStatus={video.status} />;
    case "flashcards":
      return <FlashcardsPanel videoId={videoId} videoStatus={video.status} />;
    default:
      return null;
  }
}
