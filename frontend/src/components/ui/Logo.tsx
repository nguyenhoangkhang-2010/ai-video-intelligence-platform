/**
 * Product mark: a watch case with a single play-triangle hand at the
 * twelve o'clock index - "time inside a video", not a generic AI
 * sparkle. Renders at any size via a single viewBox, in currentColor.
 */
export function Mark({ size = 22, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <circle cx="12" cy="12" r="10.2" stroke="currentColor" strokeWidth="1.8" />
      <line x1="12" y1="2.6" x2="12" y2="5" stroke="currentColor" strokeWidth="1.8" />
      <line x1="21.4" y1="12" x2="19" y2="12" stroke="currentColor" strokeWidth="1.2" />
      <line x1="12" y1="21.4" x2="12" y2="19" stroke="currentColor" strokeWidth="1.2" />
      <line x1="2.6" y1="12" x2="5" y2="12" stroke="currentColor" strokeWidth="1.2" />
      <path d="M10 8.4v7.2l5.8-3.6z" fill="currentColor" />
    </svg>
  );
}

/** Wordmark: the mark plus "REELSENSE" set as a printed dial legend. */
export function Wordmark({ className, size = 22 }: { className?: string; size?: number }) {
  return (
    <span className={className}>
      <span className="flex items-center gap-2.5">
        <Mark size={size} className="text-text-primary" />
        <span className="hidden font-display text-[0.95rem] font-semibold uppercase tracking-[0.22em] text-text-primary min-[420px]:inline">
          Reel<span className="text-accent">sense</span>
        </span>
      </span>
    </span>
  );
}
