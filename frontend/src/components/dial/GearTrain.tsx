import { Icon } from "@/components/ui/Icon";
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

// Big/small gears alternate. Same tooth depth on both, and the centre
// distance is the sum of their pitch radii, so neighbours' teeth really
// interleave instead of floating apart.
const TOOTH_DEPTH = 6;
const BIG = { outer: 40, teeth: 18, seconds: 6 };
// Small gear turns faster by the tooth ratio, like a real train.
const SMALL = { outer: 30, teeth: 14, seconds: (6 * 14) / 18 };
const PITCH = BIG.outer - TOOTH_DEPTH / 2 + (SMALL.outer - TOOTH_DEPTH / 2);
const HEIGHT = BIG.outer * 2 + 8;
// A big gear is wider than its half-pitch column: pad both ends so the
// first and last gears aren't clipped (the label grid is inset to match).
const PAD = BIG.outer - PITCH / 2 + 2;

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
 * outline. All gears sit on one axis with their teeth interleaved, so
 * the train turns as one (adjacent gears counter-rotate, the small ones
 * faster by the tooth ratio) and stops when processing completes.
 *
 * Labels are HTML, not SVG text: one grid column per gear, exactly one
 * gear pitch wide, so each label sits under its own gear, never overlaps
 * its neighbour, and keeps a readable size at any screen width (SVG text
 * scaled down with the drawing).
 */
export function GearTrain({ stages, activeIndex, complete = false, className }: GearTrainProps) {
  const width = PITCH * stages.length + PAD * 2;
  const cy = HEIGHT / 2;

  return (
    <div className={cn("mx-auto w-full max-w-xl", className)}>
      <svg
        viewBox={`0 0 ${width} ${HEIGHT}`}
        className="block w-full"
        role="img"
        aria-label={`Pipeline: ${stages.join(", ")}`}
      >
        {stages.map((stage, index) => {
          const gear = index % 2 === 0 ? BIG : SMALL;
          const inner = gear.outer - TOOTH_DEPTH;
          const cx = PAD + PITCH / 2 + index * PITCH;
          const done = complete || index < activeIndex;
          const running = !complete && index === activeIndex;
          const fill = done ? "rgb(var(--color-lume))" : running ? "rgb(var(--color-ai))" : "rgb(var(--color-surface-elevated))";
          const stroke = done || running ? "rgb(var(--color-text-primary))" : "rgb(var(--color-text-primary) / 0.45)";
          // Half a tooth of offset on every other gear so teeth fall into gaps.
          const phase = index % 2 === 0 ? 0 : 180 / gear.teeth;
          return (
            <g key={stage} transform={`translate(${cx} ${cy}) rotate(${phase})`}>
              <g
                // Meshed gears can't turn alone: the whole train runs while
                // processing and stops when done. State is shown by colour.
                className={cn(!complete && "animate-spin motion-reduce:animate-none")}
                style={{
                  transformBox: "fill-box",
                  transformOrigin: "center",
                  animationDuration: `${gear.seconds}s`,
                  animationDirection: index % 2 === 0 ? "normal" : "reverse",
                }}
              >
                <path d={gearPath(gear.teeth, gear.outer, inner)} style={{ fill, stroke }} strokeWidth={1.5} />
                <circle r={inner * 0.42} style={{ fill: "rgb(var(--color-surface-sunken))", stroke }} strokeWidth={1.5} />
                <line x1={0} y1={-inner * 0.42} x2={0} y2={-inner + 2} style={{ stroke }} strokeWidth={1.5} />
              </g>
              <circle r={3} style={{ fill: "rgb(var(--color-atmosphere))" }} />
            </g>
          );
        })}
      </svg>

      <ol
        className="mt-4 grid"
        style={{
          gridTemplateColumns: `repeat(${stages.length}, minmax(0, 1fr))`,
          paddingInline: `${(PAD / width) * 100}%`,
        }}
      >
        {stages.map((stage, index) => {
          const done = complete || index < activeIndex;
          const running = !complete && index === activeIndex;
          return (
            <li
              key={stage}
              aria-current={running ? "step" : undefined}
              className={cn(
                "flex min-w-0 flex-col items-center gap-1 px-0.5 text-center font-mono",
                done || running ? "text-text-primary" : "text-text-muted",
              )}
            >
              <span className={cn("flex items-center gap-1 text-[10px] tracking-[0.14em]", running && "text-ai")}>
                {done && <Icon name="check" size={10} />}
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                className={cn(
                  // Wraps rather than truncates: a stage name is never hidden.
                  "w-full text-[10px] uppercase leading-tight tracking-normal [overflow-wrap:anywhere] sm:text-[11px] sm:tracking-[0.06em]",
                  running && "font-semibold",
                )}
              >
                {stage}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
