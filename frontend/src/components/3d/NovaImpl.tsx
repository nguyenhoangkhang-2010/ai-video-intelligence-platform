"use client";

import { Suspense } from "react";

import { NovaErrorBoundary } from "@/components/3d/NovaErrorBoundary";
import { NovaModel } from "@/components/3d/NovaModel";
import { NovaScene, type NovaPresentationMode } from "@/components/3d/NovaScene";
import type { NovaState } from "@/components/3d/novaClips";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { cn } from "@/lib/utils";

interface NovaProps {
  state: NovaState;
  className?: string;
  onGestureEnd?: (state: NovaState) => void;
  externalPointer?: { x: number; y: number } | null;
  /**
   * "circle" (default) crops Nova into a circular avatar - correct
   * for every small/boxed placement (the ambient corner instance, the
   * old auth-panel treatment). "free" renders uncropped, full-bleed -
   * for large compositional placements where Nova is the scene itself
   * (a full-viewport login background), not an avatar inside one.
   */
  shape?: "circle" | "free";
  /** Camera presentation - see NovaScene.tsx for what each mode actually frames and why. */
  mode?: NovaPresentationMode;
}

/**
 * Nova is a supplementary visual layer, never load-bearing for any
 * workflow (see AIMessage.tsx's own text-based ThinkingIndicator,
 * which already communicates the AI Chat lifecycle without Nova) -
 * so it is always `aria-hidden` and never intercepts pointer events
 * meant for real UI underneath/around it, and a WebGL/GLB failure
 * degrades to a static glyph rather than breaking the page.
 *
 * `prefers-reduced-motion` freezes Nova on its idle pose (no gesture
 * crossfades, no cursor tracking) instead of unmounting it entirely -
 * still present as a calm visual anchor, just not moving.
 */
function NovaImpl({ state, className, onGestureEnd, externalPointer, shape = "circle", mode = "ambient" }: NovaProps) {
  const reducedMotion = useReducedMotion();

  return (
    <div
      aria-hidden="true"
      className={cn(
        "relative pointer-events-none",
        shape === "circle" ? "skeleton overflow-hidden rounded-full" : "overflow-visible",
        className,
      )}
    >
      <NovaErrorBoundary fallback={<NovaFallbackGlyph />}>
        <Suspense fallback={null}>
          <NovaScene mode={mode}>
            <NovaModel
              state={reducedMotion ? "idle" : state}
              trackPointer={!reducedMotion}
              onGestureEnd={onGestureEnd}
              externalPointer={reducedMotion ? null : externalPointer}
            />
          </NovaScene>
        </Suspense>
      </NovaErrorBoundary>
    </div>
  );
}

/** Degraded, still-on-brand visual for a GLB/WebGL failure - never a blank box. */
function NovaFallbackGlyph() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-surface-elevated">
      <span className="h-3 w-3 rounded-full bg-ai shadow-[0_0_16px_4px_rgb(var(--color-ai)/0.55)]" />
    </div>
  );
}

// default export required for React.lazy() - see Nova.tsx, the
// public, code-split entry point every call site actually imports.
export default NovaImpl;
