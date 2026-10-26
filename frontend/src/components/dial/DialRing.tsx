import type { ReactNode } from "react";

import { clamp01, polar } from "@/components/dial/geometry";
import { cn } from "@/lib/utils";

export type DialTone = "lume" | "ai" | "atmosphere" | "error" | "ink" | "success";

const TONE_VAR: Record<DialTone, string> = {
  lume: "--color-lume",
  ai: "--color-ai",
  atmosphere: "--color-atmosphere",
  error: "--color-error",
  ink: "--color-text-primary",
  success: "--color-success",
};

export function toneColor(tone: DialTone, alpha = 1): string {
  return `rgb(var(${TONE_VAR[tone]}) / ${alpha})`;
}

interface DialRingProps {
  /** Rendered diameter in px. Omit to fill the parent (use a square parent). */
  size?: number;
  /** 0..1 arc drawn on the track (a power-reserve / progress indicator). `null` hides it. */
  progress?: number | null;
  tone?: DialTone;
  /** Number of printed indices around the face (0 for none). */
  ticks?: number;
  /** Every Nth tick is drawn long (an hour index). */
  majorEvery?: number;
  /** Turn fractions (0..1) that get a carmine index dot - chapter starts, etc. */
  markers?: number[];
  /** Thickness of the case ring, in viewBox units out of 100. */
  caseWidth?: number;
  /** Raised ink case instead of titanium (active/selected state). */
  emphasized?: boolean;
  className?: string;
  children?: ReactNode;
}

/**
 * The basic watch face every dial-shaped element in the product is
 * built from: a titanium case ring, a matte face, printed indices, and
 * an optional progress arc. Pure SVG with flat fills - the same
 * drawing at 48px (a library "watch") or 600px (the workspace dial).
 * Decorative by default; callers put the real, labelled content in
 * `children`.
 */
export function DialRing({
  size,
  progress = null,
  tone = "lume",
  ticks = 60,
  majorEvery = 5,
  markers = [],
  caseWidth = 6,
  emphasized = false,
  className,
  children,
}: DialRingProps) {
  const c = 50;
  const outer = 50 - caseWidth / 2;
  const face = 50 - caseWidth;
  const track = face - 3.2;
  const circumference = 2 * Math.PI * track;
  const amount = progress === null ? null : clamp01(progress);

  return (
    <div
      className={cn("relative shrink-0", !size && "h-full w-full", className)}
      style={size ? { width: size, height: size } : undefined}
    >
      <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full overflow-visible" aria-hidden="true">
        <circle
          cx={c}
          cy={c}
          r={outer}
          fill="none"
          style={{ stroke: emphasized ? "rgb(var(--color-text-primary))" : "rgb(var(--color-case))" }}
          strokeWidth={caseWidth}
        />
        <circle cx={c} cy={c} r={face} style={{ fill: "rgb(var(--color-surface-sunken))" }} />

        {ticks > 0 &&
          Array.from({ length: ticks }).map((_, index) => {
            const t = index / ticks;
            const major = index % majorEvery === 0;
            const a = polar(c, c, face - 0.6, t);
            const b = polar(c, c, face - (major ? 4.4 : 2.2), t);
            return (
              <line
                key={index}
                x1={a.x}
                y1={a.y}
                x2={b.x}
                y2={b.y}
                style={{ stroke: "rgb(var(--color-text-primary))" }}
                strokeOpacity={major ? 0.85 : 0.35}
                strokeWidth={major ? 0.9 : 0.45}
              />
            );
          })}

        {amount !== null && (
          <>
            <circle cx={c} cy={c} r={track} fill="none" style={{ stroke: "rgb(var(--color-text-primary) / 0.1)" }} strokeWidth={1.6} />
            <circle
              cx={c}
              cy={c}
              r={track}
              fill="none"
              style={{ stroke: toneColor(tone) }}
              strokeWidth={1.6}
              strokeDasharray={circumference}
              strokeDashoffset={circumference * (1 - amount)}
              transform={`rotate(-90 ${c} ${c})`}
              className="transition-[stroke-dashoffset] duration-slow ease-calm"
            />
          </>
        )}

        {markers.map((t, index) => {
          const p = polar(c, c, face - 6.4, clamp01(t));
          return <circle key={index} cx={p.x} cy={p.y} r={1.1} style={{ fill: "rgb(var(--color-atmosphere))" }} />;
        })}
      </svg>
      {children && <div className="absolute inset-0 flex items-center justify-center">{children}</div>}
    </div>
  );
}
