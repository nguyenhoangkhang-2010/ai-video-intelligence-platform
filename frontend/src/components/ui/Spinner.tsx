import { cn } from "@/lib/utils";

/**
 * A tiny watch face whose single hand sweeps - the product's loading
 * mark, instead of a generic ring spinner. Inherits `currentColor`.
 */
export function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={cn("shrink-0 text-text-muted", className)}
      role="presentation"
      aria-hidden="true"
    >
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="1.6" />
      <line x1="12" y1="3.4" x2="12" y2="5.2" stroke="currentColor" strokeWidth="1.6" />
      <g className="origin-center animate-spin" style={{ transformBox: "view-box", animationDuration: "1.2s" }}>
        <line x1="12" y1="12" x2="12" y2="5.6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="square" />
      </g>
      <circle cx="12" cy="12" r="1.6" fill="currentColor" />
    </svg>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton rounded", className)} />;
}
