"use client";

import { lazy, Suspense } from "react";

import type { Workspace3DImplProps } from "@/components/3d/workspace3d/Workspace3DImpl";
import { cn } from "@/lib/utils";

/**
 * Public entry point for every ui-3d accent in the Workspace - the
 * real R3F/three.js implementation (Workspace3DImpl.tsx) is lazy-
 * loaded exactly like Nova (src/components/3d/Nova.tsx), for the same
 * reason: it's a genuinely large dependency (three.js + R3F + drei)
 * that a route showing no 3D accent shouldn't pay to download. Only
 * one Workspace mode panel is ever active at a time, so only one of
 * these (if any) is ever mounted alongside Nova's own ambient
 * instance - never a pile of simultaneous Canvases.
 *
 * Decorative by default: `aria-hidden` and `pointer-events-none`
 * unless a call site explicitly opts out, matching how Nova.tsx itself
 * treats its own supplementary visual layer (see NovaImpl.tsx) - none
 * of the four integrations wired up so far (pipeline progress, an AI
 * chat answer accent, a quiz right/wrong reaction, a flashcards
 * completion accent) carry information that isn't already stated in
 * real text nearby, so a screen reader loses nothing by skipping them.
 */
const Workspace3DImpl = lazy(() => import("@/components/3d/workspace3d/Workspace3DImpl"));

interface Workspace3DObjectProps extends Workspace3DImplProps {
  className?: string;
  interactive?: boolean;
}

export function Workspace3DObject({ className, interactive = false, ...implProps }: Workspace3DObjectProps) {
  return (
    <div
      aria-hidden={!interactive}
      className={cn("relative", !interactive && "pointer-events-none", className)}
    >
      <Suspense fallback={<div className="skeleton h-full w-full rounded-lg" aria-hidden="true" />}>
        <Workspace3DImpl {...implProps} />
      </Suspense>
    </div>
  );
}
