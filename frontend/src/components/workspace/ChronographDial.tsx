"use client";

import { useRef, useState, type KeyboardEvent, type PointerEvent, type ReactNode } from "react";

import { DialRing, type DialTone } from "@/components/dial/DialRing";
import { arcPath, clamp01, polar, toRoman, turnFromPoint } from "@/components/dial/geometry";
import { Icon, type IconName } from "@/components/ui/Icon";
import { useVideoPlayer } from "@/hooks/useVideoPlayer";
import { cn, formatTimecode } from "@/lib/utils";
import type { Chapter } from "@/types/chapter";

export interface SubDialDef {
  label: string;
  icon: IconName;
  tone: DialTone;
}

interface ChronographDialProps {
  /** The real video (or its loading/error state), set into the face. */
  children: ReactNode;
  chapters: Chapter[];
  /** The API's duration, used for the bezel until the <video> reports its own. */
  fallbackDuration?: number;
  subDials: SubDialDef[];
  activeSubDial: string;
  onSelectSubDial: (label: string) => void;
  /** The crown: +1 = next mode, -1 = previous mode. */
  onCrown: (direction: 1 | -1) => void;
  className?: string;
}

const VIEW = 1000;
const C = VIEW / 2;
const CASE_R = 485;
const BEZEL_R = 447;
const BEZEL_W = 46;
const FACE_R = 420;

/** Sub-dial centres as % of the dial (left, top) - a shallow arc under the video. */
const SUBDIAL_POSITIONS: Array<[number, number]> = [
  [27, 72.5],
  [42.5, 78],
  [57.5, 78],
  [73, 72.5],
];

/**
 * The workspace's centrepiece: the video is set into a chronograph
 * dial whose rotating bezel IS the timeline.
 *
 * - Bezel: a real seek control - click or drag anywhere on the band to
 *   jump there (it's also a keyboard slider: ←/→ 5s, PageUp/PageDown
 *   one chapter). Printed minute indices, a lume arc for elapsed time,
 *   carmine chapter indices (numbered in their tooltip and in the
 *   chapter strip below), and a lume playhead.
 * - Face: the real <video> (passed as children) plus a digital
 *   "date window" with the current/total timecode.
 * - Sub-dials: the four workspace groups (Watch/Understand/Ask/Study).
 * - Crown: steps to the next/previous mode (click, wheel, or ↑/↓).
 *
 * All geometry is one SVG viewBox scaled to the dial's box, so the
 * same drawing works at 340px on a phone or 800px on a desktop.
 */
export function ChronographDial({
  children,
  chapters,
  fallbackDuration = 0,
  subDials,
  activeSubDial,
  onSelectSubDial,
  onCrown,
  className,
}: ChronographDialProps) {
  const player = useVideoPlayer();
  const svgRef = useRef<SVGSVGElement>(null);
  const [dragging, setDragging] = useState(false);
  const duration = player.duration || fallbackDuration || 0;
  const progress = duration > 0 ? clamp01(player.currentTime / duration) : 0;
  const head = polar(C, C, BEZEL_R, progress);

  function seekFromPointer(event: PointerEvent<SVGElement>) {
    const svg = svgRef.current;
    if (!svg || duration <= 0) return;
    const rect = svg.getBoundingClientRect();
    const turn = turnFromPoint(
      { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
      { x: event.clientX, y: event.clientY },
    );
    player.seek(turn * duration);
  }

  function handleBezelKey(event: KeyboardEvent<SVGGElement>) {
    if (duration <= 0) return;
    const starts = chapters.map((chapter) => chapter.start_time).sort((a, b) => a - b);
    if (event.key === "ArrowRight" || event.key === "ArrowUp") player.seek(player.currentTime + 5);
    else if (event.key === "ArrowLeft" || event.key === "ArrowDown") player.seek(player.currentTime - 5);
    else if (event.key === "PageDown") {
      const next = starts.find((start) => start > player.currentTime + 0.5);
      if (next !== undefined) player.seek(next);
    } else if (event.key === "PageUp") {
      const previous = [...starts].reverse().find((start) => start < player.currentTime - 1.5);
      player.seek(previous ?? 0);
    } else if (event.key === "Home") player.seek(0);
    else if (event.key === "End") player.seek(duration);
    else return;
    event.preventDefault();
  }

  return (
    <div className={cn("relative aspect-square w-full select-none [container-type:inline-size]", className)}>
      <svg ref={svgRef} viewBox={`0 0 ${VIEW} ${VIEW}`} className="absolute inset-0 h-full w-full overflow-visible">
        {/* Case */}
        <circle cx={C} cy={C} r={CASE_R} fill="none" style={{ stroke: "rgb(var(--color-case))" }} strokeWidth={30} />
        <circle cx={C} cy={C} r={CASE_R + 15} fill="none" style={{ stroke: "rgb(var(--color-text-primary))" }} strokeWidth={2} />
        {/* Bezel band */}
        <circle cx={C} cy={C} r={BEZEL_R} fill="none" style={{ stroke: "rgb(var(--color-surface-elevated))" }} strokeWidth={BEZEL_W} />
        <circle cx={C} cy={C} r={BEZEL_R - BEZEL_W / 2} fill="none" style={{ stroke: "rgb(var(--color-text-primary))" }} strokeWidth={2} />
        {/* Face */}
        <circle cx={C} cy={C} r={FACE_R - 2} style={{ fill: "rgb(var(--color-surface-sunken))" }} />

        {/* Printed minute indices on the bezel */}
        {Array.from({ length: 60 }).map((_, index) => {
          const t = index / 60;
          const major = index % 5 === 0;
          const a = polar(C, C, BEZEL_R + BEZEL_W / 2 - 4, t);
          const b = polar(C, C, BEZEL_R + BEZEL_W / 2 - (major ? 22 : 12), t);
          return (
            <line
              key={index}
              x1={a.x}
              y1={a.y}
              x2={b.x}
              y2={b.y}
              style={{ stroke: "rgb(var(--color-text-primary))" }}
              strokeOpacity={major ? 0.9 : 0.4}
              strokeWidth={major ? 4 : 2}
            />
          );
        })}

        {/* Quarter timecodes */}
        {duration > 0 &&
          [0.25, 0.5, 0.75].map((t) => {
            const p = polar(C, C, FACE_R - 36, t);
            return (
              <text
                key={t}
                x={p.x}
                y={p.y}
                textAnchor="middle"
                dominantBaseline="middle"
                className="dial-small-hide font-mono"
                style={{ fontSize: 22, letterSpacing: "0.08em", fill: "rgb(var(--color-text-muted))" }}
              >
                {formatTimecode(duration * t)}
              </text>
            );
          })}

        {/* Elapsed arc */}
        {progress > 0.001 && (
          <path
            d={arcPath(C, C, BEZEL_R - 13, 0, progress)}
            fill="none"
            style={{ stroke: "rgb(var(--color-lume))" }}
            strokeWidth={12}
          />
        )}

        {/* Chapter indices */}
        {duration > 0 &&
          chapters.map((chapter, index) => {
            const t = clamp01(chapter.start_time / duration);
            const outer = polar(C, C, BEZEL_R + BEZEL_W / 2 - 2, t);
            const inner = polar(C, C, BEZEL_R - BEZEL_W / 2 + 2, t);
            const active = player.currentTime >= chapter.start_time && player.currentTime < chapter.end_time;
            return (
              <g key={chapter.id}>
                <title>{`${toRoman(index + 1)} · ${chapter.title} · ${formatTimecode(chapter.start_time)}`}</title>
                <line
                  x1={outer.x}
                  y1={outer.y}
                  x2={inner.x}
                  y2={inner.y}
                  style={{ stroke: "rgb(var(--color-atmosphere))" }}
                  strokeWidth={active ? 9 : 6}
                />
              </g>
            );
          })}

        {/* Playhead */}
        {duration > 0 && (
          <g transform={`translate(${head.x} ${head.y}) rotate(${progress * 360})`}>
            <path d="M 0 -30 L 16 0 L 0 30 L -16 0 Z" style={{ fill: "rgb(var(--color-lume))", stroke: "rgb(var(--color-text-primary))" }} strokeWidth={4} />
          </g>
        )}

        {/* Interactive band: click/drag to seek; also the keyboard slider. */}
        <g
          role="slider"
          tabIndex={0}
          aria-label="Bezel timeline"
          aria-valuemin={0}
          aria-valuemax={Math.round(duration)}
          aria-valuenow={Math.round(player.currentTime)}
          aria-valuetext={`${formatTimecode(player.currentTime)} of ${formatTimecode(duration)}`}
          onKeyDown={handleBezelKey}
          className="cursor-grab outline-none focus-visible:[&>circle]:[stroke:rgb(var(--color-accent)/0.35)]"
          style={{ cursor: dragging ? "grabbing" : undefined }}
        >
          <circle
            cx={C}
            cy={C}
            r={BEZEL_R}
            fill="none"
            stroke="transparent"
            strokeWidth={BEZEL_W + 30}
            pointerEvents="stroke"
            onPointerDown={(event) => {
              event.currentTarget.setPointerCapture(event.pointerId);
              setDragging(true);
              seekFromPointer(event);
            }}
            onPointerMove={(event) => {
              if (dragging) seekFromPointer(event);
            }}
            onPointerUp={(event) => {
              event.currentTarget.releasePointerCapture(event.pointerId);
              setDragging(false);
            }}
          />
        </g>
      </svg>

      {/* Legend + date window */}
      <div className="pointer-events-none absolute inset-x-0 top-[12.5%] flex flex-col items-center gap-[0.6%]">
        <span className="dial-small-hide index-label text-[clamp(8px,1.4cqw,11px)] text-text-secondary">ReelSense · RS-01</span>
        <span className="border border-text-primary/60 bg-surface-elevated px-2 py-[1px] font-mono text-[clamp(10px,1.8cqw,13px)] text-text-primary">
          {formatTimecode(player.currentTime)}
          <span className="text-text-muted"> / {formatTimecode(duration)}</span>
        </span>
      </div>

      {/* Video aperture */}
      <div className="absolute left-[17%] top-[23%] aspect-video w-[66%] overflow-hidden border-[3px] border-text-primary bg-text-primary">
        {children}
      </div>

      {/* Sub-dials */}
      {subDials.map((dial, index) => {
        const [left, top] = SUBDIAL_POSITIONS[index] ?? [50, 75];
        const active = dial.label === activeSubDial;
        return (
          <button
            key={dial.label}
            type="button"
            aria-label={dial.label}
            title={dial.label}
            aria-pressed={active}
            onClick={() => onSelectSubDial(dial.label)}
            className="group absolute aspect-square w-[14%] -translate-x-1/2 -translate-y-1/2 rounded-full focus-visible:outline-offset-4"
            style={{ left: `${left}%`, top: `${top}%` }}
          >
            <DialRing ticks={12} majorEvery={3} caseWidth={active ? 9 : 7} emphasized={active} progress={active ? 1 : null} tone={dial.tone}>
              <span className="flex flex-col items-center gap-[2px]" aria-hidden="true">
                <Icon
                  name={dial.icon}
                  size={16}
                  className={cn(
                    "transition-colors duration-fast",
                    active ? "text-text-primary" : "text-text-secondary group-hover:text-text-primary",
                  )}
                />
                <span className="dial-small-hide font-mono text-[clamp(7px,1.15cqw,10px)] uppercase tracking-[0.1em] text-text-primary">
                  {dial.label}
                </span>
              </span>
            </DialRing>
          </button>
        );
      })}

      {/* Crown */}
      <div className="absolute left-[99%] top-1/2 flex -translate-y-1/2 flex-col items-start">
        <button
          type="button"
          aria-label="Next mode"
          title="Crown — next mode (scroll or ↑/↓ to turn)"
          onClick={() => onCrown(1)}
          onWheel={(event) => onCrown(event.deltaY > 0 ? 1 : -1)}
          onKeyDown={(event) => {
            if (event.key === "ArrowDown") {
              event.preventDefault();
              onCrown(1);
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              onCrown(-1);
            }
          }}
          className="flex h-[clamp(40px,9cqw,64px)] w-[clamp(18px,3.4cqw,26px)] items-center justify-center border-2 border-text-primary bg-case transition-transform duration-fast active:translate-x-[2px]"
        >
          <span className="flex h-full w-full flex-col justify-evenly px-[3px]" aria-hidden="true">
            {Array.from({ length: 6 }).map((_, i) => (
              <span key={i} className="h-[2px] w-full bg-text-primary/70" />
            ))}
          </span>
        </button>
      </div>
    </div>
  );
}
