import { cn } from "@/lib/utils";

/** SVG path for a gear of `teeth` teeth centred at the origin. */
function gearPath(teeth: number, outer: number, inner: number): string {
  const step = (Math.PI * 2) / teeth;
  const points: string[] = [];
  for (let i = 0; i < teeth; i += 1) {
    const a = i * step;
    const corners: Array<[number, number]> = [
      [inner, a],
      [outer, a + step * 0.2],
      [outer, a + step * 0.5],
      [inner, a + step * 0.7],
    ];
    for (const [r, angle] of corners) {
      points.push(`${(r * Math.cos(angle)).toFixed(2)} ${(r * Math.sin(angle)).toFixed(2)}`);
    }
  }
  return `M ${points.join(" L ")} Z`;
}

interface GearTrainProps {
  stages: readonly string[];
  /** Index of the stage currently running; stages before it are done. */
  activeIndex: number;
  /** Everything finished (the last gear is "set", not running). */
  complete?: boolean;
  className?: string;
}

/**
 * The processing pipeline as a train of meshing gears: finished stages
 * are set in lume, the running stage turns in petrol, the rest wait in
 * outline. Gears alternate size so neighbours visibly mesh; adjacent
 * running/finished gears counter-rotate like a real train.
 */
export function GearTrain({ stages, activeIndex, complete = false, className }: GearTrainProps) {
  const pitch = 96;
  const width = pitch * (stages.length - 1) + 120;

  return (
    <div className={cn("w-full", className)}>
      <svg viewBox={`0 0 ${width} 150`} className="w-full" role="img" aria-label={`Pipeline: ${stages.join(", ")}`}>
        {stages.map((stage, index) => {
          const big = index % 2 === 0;
          const outer = big ? 40 : 30;
          const inner = outer - 6;
          const cx = 60 + index * pitch;
          const cy = big ? 62 : 58;
          const done = complete || index < activeIndex;
          const running = !complete && index === activeIndex;
          const fill = done ? "rgb(var(--color-lume))" : running ? "rgb(var(--color-ai))" : "rgb(var(--color-surface-elevated))";
          const stroke = done || running ? "rgb(var(--color-text-primary))" : "rgb(var(--color-text-primary) / 0.45)";
          return (
            <g key={stage}>
              <g transform={`translate(${cx} ${cy})`}>
                <g
                  className={cn(running && "animate-spin")}
                  style={{
                    transformBox: "fill-box",
                    transformOrigin: "center",
                    animationDuration: big ? "6s" : "4.5s",
                    animationDirection: index % 2 === 0 ? "normal" : "reverse",
                  }}
                >
                  <path d={gearPath(big ? 18 : 14, outer, inner)} style={{ fill, stroke }} strokeWidth={1.5} />
                  <circle r={inner * 0.42} style={{ fill: "rgb(var(--color-surface-sunken))", stroke }} strokeWidth={1.5} />
                  <line x1={0} y1={-inner * 0.42} x2={0} y2={-inner + 2} style={{ stroke }} strokeWidth={1.5} />
                </g>
                <circle r={3} style={{ fill: "rgb(var(--color-atmosphere))" }} />
              </g>
              <text
                x={cx}
                y={136}
                textAnchor="middle"
                className="font-mono"
                style={{
                  fontSize: 11,
                  letterSpacing: "0.14em",
                  fill: done || running ? "rgb(var(--color-text-primary))" : "rgb(var(--color-text-muted))",
                }}
              >
                {String(index + 1).padStart(2, "0")} {stage.toUpperCase()}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
