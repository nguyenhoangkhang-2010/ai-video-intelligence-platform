/**
 * The `ui-3d` kit's real, built assets (see `ui-3d/README.md` and
 * `ui-3d/manifest.json` at the repo root, and the actual files in
 * `frontend/public/models/ui/`) - node/clip names below are verified
 * by parsing each GLB's own glTF JSON directly, not assumed from the
 * README alone (three of the fourteen shipped models are wired into
 * the Workspace so far; the rest are real, audited, and available
 * through this same registry the moment a mode has a genuine, verified
 * use for one - see the integration notes in ProcessingBanner.tsx,
 * ChatPanel.tsx, QuizPanel.tsx and FlashcardsPanel.tsx for why those
 * four and not others - plus `logoMark`, wired for the initial video
 * loading skeleton in the Workspace page: a real `useVideo` fetch
 * in flight, not a decorative loop; and `uploadTray`, wired for the
 * Upload Studio's own real `isDragging`/idle state (see
 * app/(app)/library/upload/page.tsx) - not a Workspace mode, but the
 * same shared architecture applies outside /videos/[id] just as well.
 *
 * This round adds six more, each landing somewhere with zero
 * competing Canvas (so Nova + this accent never exceeds the 2-canvas
 * budget) and each still driven by real, existing state - never a
 * fabricated toggle:
 * - `statusBadges`: OverviewPanel, `visibleNodes` isolates the one
 *   `Badge_<state>` matching the real `video.status` (Overview has no
 *   other accent).
 * - `videoFrame`: FeaturedVideo (Library page) - `visibleNodes` keeps
 *   only the outer bezel (`BackPlate/Bezel/InnerLip/FrameBody`),
 *   hiding every playback-control node (`Screen/Progress/Playhead/
 *   PlayKey/SkipBack/SkipForward/Track/ChapterTick_N/EvidencePin_N/
 *   Volume/Fullscreen/Dock/AIChip nodes`) - a decorative shell around the
 *   card's own already-abstract "no real thumbnail" surface, never a
 *   second video or a duplicate control. Library has no Nova/other
 *   accent, so this is the only Canvas on that page.
 * - `chapterStrip`: ChaptersPanel's own `ProcessingState`/`EmptyState`
 *   only - i.e. exactly the moments there is no real chapter array yet
 *   to misrepresent. The real, arbitrary-length chapter timeline
 *   (once chapters exist) stays the existing HTML/CSS proportional
 *   bars - this never overlays real per-video chapter data.
 * - `buttonPrimary`/`buttonAi`/`buttonSecondary`: a real native
 *   `<button>` (all its own keyboard/focus/aria/click behavior
 *   untouched) with this model as a purely decorative,
 *   `aria-hidden`/`pointer-events-none` layer underneath, driven by
 *   real `onMouseEnter/onFocus`->`holdActive` and real `onMouseDown`->
 *   `playKey` - see Button3D.tsx. Placed only where nothing else
 *   already occupies the budget: the auth pages' primary submit
 *   (`buttonPrimary`, alongside Nova's own hero canvas), Search's
 *   submit (`buttonAi`, whose real "Thinking" clip gates on
 *   `search.isPending` - Search has no other accent), and Upload
 *   Studio's "Cancel upload" (`buttonSecondary`, shown only in the
 *   "uploading" stage, when `uploadTray` - idle-stage only - is
 *   already unmounted).
 *
 * Evaluated and still NOT integrated, with the specific technical
 * reason on record:
 * - `rs_icons.glb`: parsed directly - zero animation clips across all
 *   41 icon nodes. A static shape with no motion or interactivity
 *   provides no functional or visual advantage over the existing
 *   `Icon.tsx` SVG system (same silhouette, extra GPU/Canvas cost),
 *   so there is no real screen this makes better rather than just
 *   heavier. Kept for future work that would actually animate an icon.
 * - `rs_icon_keys.glb`: parsed directly - 18 keys whose node names
 *   (`Key_video/chapters/transcript/summary/translate/chat/search/
 *   quiz/flashcard/upload/play/pause/skip-back/skip-forward/volume/
 *   fullscreen/download/refresh`) map almost 1:1 onto this product's
 *   real interactive surface (Workspace modes + player controls), and
 *   its one `Ripple` clip animates ALL keycaps together, not any one
 *   individually - this is clearly built for a "keyboard shortcuts"
 *   overview, a real feature this product doesn't have yet (the real
 *   shortcuts - arrow keys, space/enter - exist in code but are never
 *   surfaced to a user anywhere). Building that surface is a new
 *   product feature, not a GLB-integration task; kept for when one
 *   exists.
 */
export type Workspace3DModelName =
  | "pipeline"
  | "aiAnswer"
  | "quizCard"
  | "flashcards"
  | "logoMark"
  | "uploadTray"
  | "statusBadges"
  | "videoFrame"
  | "chapterStrip"
  | "buttonPrimary"
  | "buttonAi"
  | "buttonSecondary";

interface Workspace3DModelDef {
  path: string;
  /** Real clip name(s) this model ships, from the GLB's own animations array. */
  clips: string[];
}

export const WORKSPACE_3D_MODELS: Record<Workspace3DModelName, Workspace3DModelDef> = {
  pipeline: { path: "/models/ui/rs_pipeline.glb", clips: ["Process"] },
  aiAnswer: { path: "/models/ui/rs_ai_answer.glb", clips: ["Answer"] },
  quizCard: { path: "/models/ui/rs_quiz_card.glb", clips: ["Answer_Correct", "Answer_Wrong"] },
  flashcards: { path: "/models/ui/rs_flashcards.glb", clips: ["Flip", "Float"] },
  logoMark: { path: "/models/ui/rs_logo_mark.glb", clips: ["Float", "Signal"] },
  uploadTray: { path: "/models/ui/rs_upload_tray.glb", clips: ["Idle", "Drop"] },
  statusBadges: { path: "/models/ui/rs_status_badges.glb", clips: ["Pulse"] },
  videoFrame: { path: "/models/ui/rs_video_frame.glb", clips: ["Playback", "Intro", "Hover_Play", "AI_Live"] },
  chapterStrip: { path: "/models/ui/rs_chapter_strip.glb", clips: ["Scan"] },
  buttonPrimary: { path: "/models/ui/rs_button_primary.glb", clips: ["Hover", "Press"] },
  buttonAi: { path: "/models/ui/rs_button_ai.glb", clips: ["Hover", "Press", "Thinking"] },
  buttonSecondary: { path: "/models/ui/rs_button_secondary.glb", clips: ["Hover", "Press"] },
};

/**
 * rs_status_badges.glb's three baked variant *groups* (verified node
 * names) - each nested one level under the model's own scene root, not
 * a flat sibling of it, which is why hiding by name (see
 * Workspace3DImpl.tsx's `hideNodes`, using `getObjectByName` rather
 * than only checking direct children) is required, not optional.
 */
export const STATUS_BADGE_GROUPS = {
  processing: "Badge_Processing",
  ready: "Badge_Ready",
  failed: "Badge_Failed",
} as const;

/** For a given real state, the other two groups to hide - see OverviewPanel.tsx. */
export function statusBadgeHideNodes(active: keyof typeof STATUS_BADGE_GROUPS): string[] {
  return Object.entries(STATUS_BADGE_GROUPS)
    .filter(([key]) => key !== active)
    .map(([, name]) => name);
}

/**
 * rs_video_frame.glb's own playback-control geometry, hidden so only
 * its outer bezel (BackPlate/Bezel/InnerLip/FrameBody) shows - see
 * registry.ts's module comment for why (a decorative shell, never a
 * duplicate/fake video control).
 */
export const VIDEO_FRAME_CONTROL_NODES = [
  "Screen",
  "Progress",
  "Playhead",
  "PlayKey",
  "PlayKeyBody",
  "PlayIcon",
  "SkipBack",
  "SkipForward",
  "Track",
  "ChapterTick_0",
  "ChapterTick_1",
  "ChapterTick_2",
  "EvidencePin_0",
  "EvidencePin_1",
  "Volume",
  "Fullscreen",
  "Dock",
  "DockBody",
  "AIChip",
  "AIChipBody",
  "AIChipDot",
];

/**
 * rs_pipeline.glb's 5 real stages (Ingest/Transcribe/Understand/Index/
 * Ready - verified node names: Stage_<name>/Lit_<name>/StageCap_<name>,
 * plus RailFill_0..3 connecting them). The backend's own
 * ProcessingJob.current_step (app/pipelines/video_pipeline.py) has 10
 * granular real step strings, not 5 - this maps each real step onto
 * the model's coarser 5-stage visual, so the model always reflects a
 * genuine backend state, never an invented one. A step not in this map
 * (there shouldn't be one, but pipelines evolve) falls back to stage 0
 * rather than crashing.
 */
export const PIPELINE_STAGE_NAMES = ["Ingest", "Transcribe", "Understand", "Index", "Ready"] as const;

export const PIPELINE_STEP_TO_STAGE: Record<string, number> = {
  "Extract Metadata": 0,
  "Preparing Transcription": 1,
  Transcribing: 1,
  "Saving Transcript": 1,
  "Generating Summary": 2,
  "Generating Translation": 2,
  "Detecting Chapters": 2,
  "Generating Quiz": 2,
  "Generating Flashcards": 2,
  "Generating Embeddings": 3,
  Completed: 4,
};
