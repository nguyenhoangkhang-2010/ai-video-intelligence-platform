"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

/**
 * Coordinates the Workspace's ONE shared "second Canvas" slot (Nova
 * being the first) between the real video frame (rs_video_frame.glb,
 * wrapping the actual `<video>` in the video column) and whichever
 * mode panel's own accent is currently mounted in the content column
 * (OverviewPanel's status badge, ChaptersPanel's chapter-strip motif,
 * SearchPanel's button skin, a Quiz/Chat/Flashcards reaction) - both
 * columns are visible at once in the real side-by-side layout, so
 * without this, a mode accent appearing while the video frame is also
 * showing would be a real 3rd simultaneous WebGL context, over the
 * project's hard 2-canvas budget (Nova + one shared accent).
 *
 * Real, not simulated coordination: each accent consumer calls
 * `useAccentSlotClaim(isMyAccentActuallyMounted)` for as long as ITS
 * OWN Workspace3DObject is genuinely in the DOM (not just "my panel is
 * active" - e.g. Quiz only claims once a real answer produced a
 * reaction). The video frame reads `useAccentSlotFree()` and only
 * renders while nothing else holds the slot, yielding instantly the
 * moment one does and reappearing the moment it releases.
 */
const AccentSlotContext = createContext<{
  claim: () => void;
  release: () => void;
  isFree: boolean;
} | null>(null);

export function AccentSlotProvider({ children }: { children: ReactNode }) {
  const [count, setCount] = useState(0);
  const claim = () => setCount((current) => current + 1);
  const release = () => setCount((current) => Math.max(0, current - 1));

  return (
    <AccentSlotContext.Provider value={{ claim, release, isFree: count === 0 }}>{children}</AccentSlotContext.Provider>
  );
}

/** Call with whether this component's own Workspace3DObject is currently mounted - claims/releases the shared slot automatically as that changes. */
export function useAccentSlotClaim(active: boolean): void {
  const ctx = useContext(AccentSlotContext);
  useEffect(() => {
    if (!ctx || !active) return;
    ctx.claim();
    return () => ctx.release();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ctx, active]);
}

/** True while no mode-panel accent currently holds the shared slot - safe for the video frame (or anything else sharing it) to render. Outside the provider, defaults to true (frees callers from needing to guard against a missing provider). */
export function useAccentSlotFree(): boolean {
  const ctx = useContext(AccentSlotContext);
  return ctx?.isFree ?? true;
}
