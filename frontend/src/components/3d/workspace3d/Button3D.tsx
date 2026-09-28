"use client";

import { useState, type ComponentProps } from "react";

import { Workspace3DObject } from "@/components/3d/workspace3d/Workspace3DObject";
import { Button } from "@/components/ui/Button";
import { cn } from "@/lib/utils";

type GlbButtonModel = "buttonPrimary" | "buttonAi" | "buttonSecondary";

/**
 * The real text color each model's own pill surface needs for
 * contrast (see ui-3d/README.md's Files table): buttonPrimary/buttonAi
 * are solid cobalt/teal fills (white text), buttonSecondary is a
 * porcelain pill with a cobalt rim (dark text) - matching the same
 * tokens Button.tsx's own primary/ai/secondary variants already use.
 */
const GLB_BUTTON_TEXT_CLASS: Record<GlbButtonModel, string> = {
  buttonPrimary: "text-accent-on",
  buttonAi: "text-ai-on",
  buttonSecondary: "text-text-primary",
};

interface Button3DProps extends ComponentProps<typeof Button> {
  glbModel: GlbButtonModel;
  /** Real ongoing async state - only rs_button_ai ships a matching "Thinking" clip; ignored for the other two models. */
  thinking?: boolean;
}

/**
 * ONE native `<button>` is both the real interactive element AND the
 * only visible button - there is no second, competing HTML button
 * rendered beside it. The ui-3d model IS this button's own visual
 * body (an absolutely-positioned, `aria-hidden`/`pointer-events-none`
 * layer filling the exact same box, painted first so the real label
 * sits on top of it) rather than a decorative accent floating next to
 * a separately-styled HTML button - `variant="unstyled"` strips
 * Button's own background/border/shadow, leaving just the real shape,
 * sizing, focus ring and disabled/cursor handling every other variant
 * already gets, with the GLB providing the surface color and shape
 * instead of a CSS fill.
 *
 * The GLB reacts only to this SAME button's real DOM state - never an
 * interaction layer of its own:
 * - hover/focus-visible -> `holdActive` (the model's own "Hover" clip,
 *   played forward and clamped, or reversed back to rest - see
 *   Workspace3DImpl.tsx's hold mode and the kit's own documented
 *   "reverse a hover with timeScale = -1" pattern).
 * - a real pointerdown -> a fresh one-shot "Press" clip.
 * - `disabled` -> the GLB layer dims with the button, same as any
 *   other variant's own disabled treatment.
 * - `thinking` (rs_button_ai only) -> its own "Thinking" loop, gated
 *   by the caller's real async state (e.g. a pending RAG/search
 *   request) - never a fabricated toggle.
 * - real Enter/Space activation already works for free - it's a real
 *   `<button>`, no separate key handling needed.
 *
 * No new Canvas budget rule of its own: each call site is chosen
 * specifically because nothing else already occupies the 2-canvas
 * (Nova + one accent) budget there - see registry.ts's module comment.
 */
export function Button3D({
  glbModel,
  thinking,
  onMouseEnter,
  onMouseLeave,
  onFocus,
  onBlur,
  onMouseDown,
  disabled,
  isLoading,
  className,
  children,
  ...props
}: Button3DProps) {
  const [hovered, setHovered] = useState(false);
  const [focused, setFocused] = useState(false);
  const [pressKey, setPressKey] = useState(0);
  const isDisabled = disabled || isLoading;

  return (
    <Button
      variant="unstyled"
      disabled={disabled}
      isLoading={isLoading}
      className={cn("relative isolate overflow-hidden", GLB_BUTTON_TEXT_CLASS[glbModel], className)}
      onMouseEnter={(event) => {
        setHovered(true);
        onMouseEnter?.(event);
      }}
      onMouseLeave={(event) => {
        setHovered(false);
        onMouseLeave?.(event);
      }}
      onFocus={(event) => {
        setFocused(true);
        onFocus?.(event);
      }}
      onBlur={(event) => {
        setFocused(false);
        onBlur?.(event);
      }}
      onMouseDown={(event) => {
        setPressKey((key) => key + 1);
        onMouseDown?.(event);
      }}
      {...props}
    >
      {/*
       * The button's own visual body, not a sibling accent - painted
       * first (behind the real label via `-z-10` inside this `isolate`
       * button, so the stacking stays scoped to just this button
       * rather than escaping behind page content). Positioning lives
       * on this own wrapper span, not passed as a className to
       * Workspace3DObject directly - its own root is unconditionally
       * `relative`, and Tailwind's generated stylesheet order doesn't
       * reliably let a consumer-supplied `absolute` beat that base
       * class in the same merged class list (the same real bug already
       * found and fixed for Nova's own positioning).
       */}
      <span className={cn("pointer-events-none absolute inset-0 -z-10", isDisabled && "opacity-50")} aria-hidden="true">
        <Workspace3DObject
          model={glbModel}
          holdClip="Hover"
          holdActive={!isDisabled && (hovered || focused)}
          playClip="Press"
          playKey={pressKey}
          loopClip={glbModel === "buttonAi" && thinking ? "Thinking" : undefined}
          className="h-full w-full"
        />
      </span>
      {children}
    </Button>
  );
}
