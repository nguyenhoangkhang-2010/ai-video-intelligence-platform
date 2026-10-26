"use client";

import { lazy, Suspense } from "react";

import type { NovaPresentationMode } from "@/components/3d/NovaScene";
import type { NovaState } from "@/components/3d/novaClips";
import { cn } from "@/lib/utils";

interface NovaProps {
  state: NovaState;
  className?: string;
  onGestureEnd?: (state: NovaState) => void;
  externalPointer?: { x: number; y: number } | null;
  shape?: "circle" | "free";
  mode?: NovaPresentationMode;
}

/**
 * Public entry point every call site imports. The real implementation
 * (three.js + @react-three/fiber + @react-three/drei, a genuinely
 * large dependency) is code-split via React.lazy rather than bundled
 * into every route's initial JS - measured impact of NOT doing this:
 * the video workspace route's First Load JS went from ~141 kB to
 * ~396 kB in `next build` once Nova was wired into ChatPanel. Lazy-
 * loading means that cost is only paid by someone who actually opens
 * a route Nova appears on, loaded async while the rest of the page
 * (e.g. the chat input, already interactive) doesn't wait for it.
 */
const NovaImpl = lazy(() => import("@/components/3d/NovaImpl"));

export function Nova({ className, shape = "circle", ...props }: NovaProps) {
  return (
    <Suspense
      fallback={
        <div aria-hidden="true" className={cn(shape === "circle" && "skeleton rounded-full", className)} />
      }
    >
      <NovaImpl className={className} shape={shape} {...props} />
    </Suspense>
  );
}
