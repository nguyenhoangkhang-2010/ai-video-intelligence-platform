"use client";

import { lazy, Suspense } from "react";

import type { MovementImplProps } from "@/components/3d/horology/MovementImpl";
import { DialRing } from "@/components/dial/DialRing";
import { cn } from "@/lib/utils";

/**
 * Public entry point for the 3D watch movement. Like Nova, the real
 * three.js implementation is code-split so routes that never show it
 * don't pay for it; while it loads, a flat 2D dial stands in.
 */
const MovementImpl = lazy(() => import("@/components/3d/horology/MovementImpl"));

export function Movement3D({ className, ...props }: MovementImplProps) {
  return (
    <Suspense
      fallback={
        <div aria-hidden="true" className={cn("flex items-center justify-center", className)}>
          <div className="aspect-square w-1/2 max-w-[320px]">
            <DialRing ticks={60} />
          </div>
        </div>
      }
    >
      <MovementImpl className={className} {...props} />
    </Suspense>
  );
}
