import { cn } from "@/lib/utils";

/**
 * Product mark: a frame notch (video) intersected by a signal line
 * (analysis/intelligence) — deliberately not a generic "AI sparkle"
 * or abstract blob. Renders at any size via a single viewBox.
 */
export function Mark({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      className={className}
      aria-hidden="true"
    >
      <rect x="1.5" y="4" width="21" height="16" rx="3.5" stroke="currentColor" strokeWidth="1.6" />
      <path
        d="M5 15.5 8.6 11l3 3.2L14 9l5 5.5"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function Logo({ className, markClassName }: { className?: string; markClassName?: string }) {
  return (
    <div className={cn("flex items-center gap-2 text-text-primary", className)}>
      <Mark className={cn("text-accent", markClassName)} />
      <span className="font-display text-heading-sm font-semibold tracking-tight">
        Reel<span className="text-accent">Sense</span>
      </span>
    </div>
  );
}
