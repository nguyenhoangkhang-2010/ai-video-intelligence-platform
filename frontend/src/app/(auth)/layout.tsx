"use client";

import { useEffect } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Nova } from "@/components/3d/Nova";
import { Mark } from "@/components/ui/Logo";

/**
 * A decorative signal trace — a static, abstract line motif evoking
 * "something is being read/analyzed", never a rendering of real audio
 * or waveform data (no such data exists at this unauthenticated
 * screen, and this shape isn't derived from any).
 */
function SignalTrace() {
  return (
    <svg
      viewBox="0 0 600 120"
      preserveAspectRatio="none"
      className="pointer-events-none absolute inset-x-0 top-[62%] h-[90px] w-full text-ai/[0.14]"
      aria-hidden="true"
    >
      <path
        d="M0 60 L80 60 L100 24 L124 96 L150 60 L210 60 L228 40 L246 60 L420 60 L444 18 L466 60 L600 60"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        vectorEffect="non-scaling-stroke"
      />
    </svg>
  );
}

/**
 * A cinematic entrance, not a split-screen "branding left / form
 * right" SaaS template: Nova is the entire scene (full-bleed,
 * uncropped - see `shape="free"` on Nova/NovaImpl), the headline sits
 * in a scrim-backed zone so it stays legible wherever Nova's
 * silhouette actually falls, and the auth form floats as a translucent
 * glass surface over the same space rather than living in its own
 * boxed column. Nova's state is the shared, product-wide
 * NovaAttentionContext (see NovaAttentionContext.tsx) - this layout
 * fires the one-time arrival "greeting" gesture, and LoginPage/
 * RegisterPage drive it further from there (focus/submit/success) so
 * Nova is genuinely reacting to what's happening on the form, not
 * playing a single fixed animation regardless of interaction.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { state, notice } = useNovaAttention();

  useEffect(() => {
    notice("greeting");
    // Fire once on arrival only - the gesture itself is one-shot and
    // the mixer crossfades back to Idle_Breathe on its own when it
    // finishes (see NovaModel.tsx), independent of this context value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="gradient-atmosphere relative min-h-screen w-full overflow-hidden">
      <Nova state={state} shape="free" mode="hero" className="absolute inset-0 z-0 opacity-95" />

      <SignalTrace />

      {/* Legibility scrim - guarantees contrast for the headline and floating form regardless of exactly where Nova's silhouette renders at a given viewport size. */}
      <div
        className="pointer-events-none absolute inset-0 z-[2] bg-[linear-gradient(115deg,rgb(var(--color-bg)/0.92)_0%,rgb(var(--color-bg)/0.5)_38%,rgb(var(--color-bg)/0.18)_62%,rgb(var(--color-bg)/0.72)_100%)]"
        aria-hidden="true"
      />

      <div className="relative z-10 flex min-h-screen w-full flex-col">
        <header className="flex items-center gap-2 px-6 pt-6 text-text-primary sm:px-10 sm:pt-8">
          <Mark size={24} className="text-accent" />
          <span className="font-display text-heading-sm font-semibold tracking-tight">
            Reel<span className="text-ai">Sense</span>
          </span>
        </header>

        <div className="flex flex-1 flex-col justify-center gap-10 px-6 py-10 sm:px-10 lg:flex-row lg:items-center lg:justify-between lg:gap-16">
          <div className="max-w-xl animate-rise lg:pb-10">
            <p className="text-label font-medium uppercase tracking-[0.16em] text-accent">AI Media Intelligence</p>
            <p className="mt-3 font-display text-hero font-semibold text-text-primary">
              Understand
              <br />
              every <span className="text-ai">frame.</span>
            </p>
            <p className="mt-6 max-w-sm text-body text-text-secondary">
              Transcripts, summaries, chapters, and grounded answers — generated from your footage, not assumed.
              A video intelligence environment, with Nova inside it.
            </p>
          </div>

          <div
            className="surface-glass w-full max-w-[380px] shrink-0 animate-rise rounded-2xl p-7 sm:p-8"
            style={{ animationDelay: "90ms" }}
          >
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
