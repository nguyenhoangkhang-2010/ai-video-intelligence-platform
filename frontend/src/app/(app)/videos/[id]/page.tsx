"use client";

import { useParams } from "next/navigation";
import { useMemo, useState, type ReactNode, type UIEvent } from "react";

import { Nova } from "@/components/3d/Nova";
import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { AccentSlotProvider, useAccentSlotFree } from "@/components/3d/workspace3d/AccentSlotContext";
import { VIDEO_FRAME_CONTROL_NODES } from "@/components/3d/workspace3d/registry";
import { ErrorState } from "@/components/ui/ErrorState";
import { Skeleton } from "@/components/ui/Spinner";
import { atmosphereGradient, SECTION_ATMOSPHERE } from "@/components/workspace/atmosphere";
import { ChapterStrip } from "@/components/workspace/ChapterStrip";
import { ProcessingBanner } from "@/components/workspace/ProcessingBanner";
import { WorkspaceHeader } from "@/components/workspace/WorkspaceHeader";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";
import type { WorkspaceSection } from "@/components/workspace/sections";
import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
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
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6">
        {/*
         * A real brand-loading moment, not decoration for its own sake -
         * this only ever renders while `useVideo`'s fetch is genuinely
         * in flight, and unmounts the instant real data (or an error)
         * arrives, same "gone once the real state moves on" pattern as
         * ProcessingBanner. Nothing else in the Workspace uses the logo
         * mark, so this stays a single, deliberate brand touch instead
         * of scattering it everywhere.
         */}
        <Workspace3DObject model="logoMark" loopClip="Float" className="h-16 w-16 opacity-70" />
        <div className="flex w-full flex-col gap-4">
          <Skeleton className="h-14 w-full" />
          <Skeleton className="flex-1" />
        </div>
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
      <AccentSlotProvider>
      <div className="flex h-full flex-col overflow-hidden">
        <WorkspaceHeader video={video.data} />
        <ProcessingBanner video={video.data} />

        {/*
         * Desktop (lg+): video and content are two real columns, not a
         * stack - video ~58%, content ~42% (`lg:basis-*` below), each
         * owning its own scroll independently. Below lg: the same two
         * blocks stack vertically instead, each still independently
         * bounded/scrollable - not the single shared-scroll-container
         * hack this used to need.
         *
         * That old hack existed because the video's own aspect-video box
         * sized purely from WIDTH, with no regard for vertical space,
         * and could demand more height than was available, collapsing
         * the panel area below it to a literal 0px. That root cause is
         * now fixed at the SOURCE instead (VideoPlayer.tsx caps itself
         * at `max-h-[42vh]`, regardless of what layout it's placed in),
         * so this wrapper no longer needs to force everything through
         * one shared scroll container as a workaround - video and
         * content can safely be two independent regions again, which is
         * what a real side-by-side layout needs anyway.
         */}
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden lg:flex-row lg:gap-5 lg:overflow-hidden lg:p-5">
          {/* Video column - the primary visual anchor, ~58% width on desktop. */}
          <div className="relative shrink-0 overflow-y-auto border-b border-border bg-bg-secondary px-5 py-7 sm:px-8 sm:py-9 lg:basis-[58%] lg:shrink-0 lg:grow-0 lg:overflow-visible lg:rounded-2xl lg:border lg:border-border lg:bg-bg-secondary lg:p-6">
            <div
              className="pointer-events-none absolute inset-0 opacity-70 lg:rounded-2xl"
              style={{
                background:
                  "radial-gradient(ellipse 900px 500px at 50% -10%, rgb(var(--color-accent) / 0.1), transparent 60%)",
              }}
              aria-hidden="true"
            />
            <div className="relative mx-auto flex w-full max-w-5xl flex-col gap-3 lg:max-w-none">
              <VideoFrameShell>
                <VideoPlayer src={streamUrl} title={video.data.title} chapters={chapterList} />
              </VideoFrameShell>
              {chapterList.length > 0 && <ChapterStrip chapters={chapterList} />}
            </div>
          </div>

          {/* Content column - mode nav + active panel, own scroll, own bounded height. */}
          <div className="relative flex min-h-0 flex-1 flex-col overflow-hidden lg:basis-[42%] lg:grow lg:rounded-2xl lg:border lg:border-border lg:bg-surface">
            <WorkspaceNav
              active={activeSection}
              onSelect={handleSelectSection}
              compact={navCompact}
              className="sticky top-0 z-20 shrink-0 lg:rounded-t-2xl"
            />

            {/*
             * Nova's workspace presence - anchored to this OUTER,
             * non-scrolling content-column wrapper (not the inner
             * scrollable panel div below) specifically so it never
             * needs to compete in z-order with panel content: every
             * panel's own heading starts right at the top of that
             * scrollable area, exactly where a "top-right" placement
             * would otherwise sit, so anything sharing that scrolling
             * context would either have to hide behind the panel's
             * opaque background (invisible in practice) or float above
             * it (covering real content). Sitting outside the scroll
             * boundary entirely avoids that dilemma: Nova stays a
             * constant, small, `pointer-events-none` presence next to
             * the nav row, and the panel underneath scrolls completely
             * independently of it. Hidden below `lg`, where the column
             * is too narrow to spare the width beside the nav labels.
             *
             * Positioning lives on THIS wrapper div, not on <Nova>
             * itself - NovaImpl's own root is unconditionally `relative`
             * (see NovaImpl.tsx), and Tailwind's generated stylesheet
             * order means a consumer-supplied `absolute` in the same
             * class list does NOT reliably beat that base `relative`
             * (found live: Nova rendered pinned to its in-flow position
             * near the nav labels instead of the intended corner).
             * NovaAmbient.tsx already establishes the correct pattern -
             * wrap Nova in your own positioned box, let Nova itself just
             * fill it - so this follows that same one instead of
             * inventing a second way to position Nova.
             */}
            <div className="pointer-events-none absolute right-3 top-2 z-30 hidden h-14 w-14 opacity-80 lg:block">
              <Nova state={novaState} mode="workspace" className="h-full w-full" />
            </div>

            <div
              className="relative min-h-[360px] flex-1 overflow-y-auto"
              onScroll={handleContentScroll}
            >
              {atmosphere && (
                <div
                  className="pointer-events-none absolute inset-0 z-0 transition-[background] duration-slow"
                  style={{ background: atmosphere }}
                  aria-hidden="true"
                />
              )}

              <div className="relative z-10 mx-auto h-full w-full max-w-5xl px-1">
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
      </div>
      </AccentSlotProvider>
    </VideoPlayerProvider>
  );
}

/**
 * rs_video_frame.glb wrapping the REAL, currently-open `<video>` - not
 * a card somewhere else with the video rendered separately. Sized
 * purely by CSS containment, not a fixed pixel box: this wrapper has
 * no width/height of its own, so it shrink-wraps to `children`'s own
 * real rendered size (VideoPlayer's own `aspect-video max-h-[42vh]
 * w-auto` sizing) via normal block layout, and the frame - an
 * absolutely-positioned sibling with `inset: 0` on the nearest
 * positioned ancestor - always exactly matches that box with no
 * separate measurement/ResizeObserver code: a real window resize (or
 * the video's own aspect ratio loading in) changes VideoPlayer's
 * rendered box, which changes this wrapper's box (CSS layout, live),
 * which changes what `inset-0` resolves to, and R3F's own Canvas
 * already re-observes its element's size on every resize - the
 * existing bounding-box auto-fit in Workspace3DImpl.tsx (already
 * built for exactly this) then reframes the model on the next frame.
 *
 * Only rendered while `useAccentSlotFree()` is true - see
 * AccentSlotContext.tsx: the video column is always visible alongside
 * whichever content-column panel is active, and some panels mount
 * their own real accent (Overview's status badge, Search's button
 * skin, a Quiz/Chat/Flashcards reaction) - without yielding, a mode
 * accent appearing while this frame also showed would be a genuine
 * 3rd simultaneous Canvas, over the project's 2-canvas budget. The
 * frame disappears the instant such an accent claims the slot and
 * reappears the instant it's released - never a 3rd context, even
 * momentarily.
 */
function VideoFrameShell({ children }: { children: ReactNode }) {
  const frameIsFree = useAccentSlotFree();

  return (
    <div className="relative mx-auto w-fit rounded-2xl shadow-lg ring-1 ring-black/[0.06]">
      {frameIsFree && (
        <div
          className="pointer-events-none absolute -inset-3 sm:-inset-4"
          style={{ zIndex: -1 }}
          aria-hidden="true"
        >
          <Workspace3DObject model="videoFrame" hideNodes={VIDEO_FRAME_CONTROL_NODES} className="h-full w-full" />
        </div>
      )}
      <div className="overflow-hidden rounded-2xl">
        {children}
      </div>
    </div>
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
