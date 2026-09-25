import Link from "next/link";

import { Nova } from "@/components/3d/Nova";
import { Icon } from "@/components/ui/Icon";
import { Mark } from "@/components/ui/Logo";
import { ROUTES } from "@/lib/constants";

/**
 * The unauthenticated arrival experience — a real page, not a
 * redirect straight to /login. Nova is the visual identity of the
 * hero (full-bleed, uncropped), and each section below states a real
 * product capability with a composition suited to that capability
 * (a proportional segment bar for chaptering, a command-bar replica
 * for search, layered cards for study) rather than one repeated
 * centered-card template. No section shows fabricated AI output as if
 * it were real extracted content - the illustrations are abstract/
 * geometric or generically labeled, never a fake transcript/summary.
 */
export function Landing() {
  return (
    <div className="relative w-full overflow-hidden">
      <div className="gradient-atmosphere absolute inset-0 -z-10 h-[130vh]" aria-hidden="true" />

      <header className="relative z-20 flex items-center justify-between px-6 py-6 sm:px-10">
        <div className="flex items-center gap-2 text-text-primary">
          <Mark size={24} className="text-accent" />
          <span className="font-display text-heading-sm font-semibold tracking-tight">
            Reel<span className="text-ai">Sense</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href={ROUTES.login}
            className="text-body-sm font-medium text-text-secondary transition-colors duration-fast hover:text-text-primary"
          >
            Sign in
          </Link>
          <Link
            href={ROUTES.register}
            className="rounded bg-accent px-3.5 py-1.5 text-body-sm font-medium text-accent-on transition-colors duration-fast hover:bg-accent-hover"
          >
            Get started
          </Link>
        </div>
      </header>

      {/* Hero — Nova full-bleed as the scene itself, typography floating over it. */}
      <section className="relative flex min-h-[86vh] w-full flex-col justify-center px-6 sm:px-10">
        <Nova state="idle" shape="free" mode="hero" className="pointer-events-none absolute inset-0 z-0" />
        <div
          className="pointer-events-none absolute inset-0 z-[1] bg-[linear-gradient(100deg,rgb(var(--color-bg)/0.88)_0%,rgb(var(--color-bg)/0.4)_45%,rgb(var(--color-bg)/0.15)_65%,rgb(var(--color-bg)/0.65)_100%)]"
          aria-hidden="true"
        />

        <div className="relative z-10 max-w-2xl animate-rise">
          <p className="text-label font-medium uppercase tracking-[0.18em] text-accent">AI Media Intelligence</p>
          <h1 className="mt-4 font-display text-hero font-semibold leading-[0.98] text-text-primary">
            Understand every
            <br />
            second of <span className="text-ai">video.</span>
          </h1>
          <p className="mt-6 max-w-md text-body-lg text-text-secondary">
            Upload a video and ReelSense transcribes, summarizes, translates, and indexes it — so you can search,
            ask, and study what was actually said, with Nova as your guide through it.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link
              href={ROUTES.register}
              className="rounded-full bg-accent px-6 py-3 text-body font-medium text-accent-on shadow-glow-primary transition-colors duration-fast hover:bg-accent-hover"
            >
              Get started free
            </Link>
            <Link
              href={ROUTES.login}
              className="rounded-full border border-border-strong px-6 py-3 text-body font-medium text-text-primary transition-colors duration-fast hover:border-accent"
            >
              Sign in
            </Link>
          </div>
        </div>
      </section>

      {/* Section 1 — Analyze/chaptering. Asymmetric split: editorial text
          left, a proportional segment bar right (the same visual idea
          as the workspace's own chapter timeline, drawn abstractly -
          no fake titles, just the shape of "one upload becomes ordered
          segments"). */}
      <section className="relative z-10 border-t border-border bg-bg px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto grid max-w-5xl grid-cols-1 items-center gap-12 lg:grid-cols-[1fr_1fr]">
          <div>
            <p className="text-label font-semibold uppercase tracking-wide text-accent">01 — Analyze</p>
            <h2 className="mt-3 font-display text-display-lg font-semibold leading-tight text-text-primary">
              Every frame,
              <br />
              transcribed and structured.
            </h2>
            <p className="mt-5 max-w-md text-body leading-relaxed text-text-secondary">
              Upload finishes, and the pipeline takes over: Whisper transcribes what was said, and the video is
              broken into chapters automatically — no manual tagging, no scrubbing through footage to find a
              moment.
            </p>
          </div>
          <div className="flex flex-col gap-3">
            <div className="flex w-full gap-[3px]">
              {[18, 26, 14, 22, 20].map((width, index) => (
                <div
                  key={index}
                  style={{ width: `${width}%` }}
                  className={index === 1 ? "h-16 rounded-md bg-accent sm:h-20" : "h-16 rounded-md bg-surface-elevated sm:h-20"}
                />
              ))}
            </div>
            <div className="flex items-center justify-between text-caption text-text-muted">
              <span className="font-mono">0:00</span>
              <span className="flex items-center gap-1.5 font-medium text-accent">
                <Icon name="chapters" size={12} /> 5 chapters detected
              </span>
              <span className="font-mono">42:18</span>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2 — Understand (summary/translation). A large centered
          statement, not a split - a different rhythm from section 1. */}
      <section className="relative z-10 border-t border-border bg-bg-secondary px-6 py-20 text-center sm:px-10 sm:py-28">
        <div className="mx-auto max-w-3xl">
          <p className="text-label font-semibold uppercase tracking-wide text-accent">02 — Understand</p>
          <p className="mt-5 font-display text-display-lg font-medium leading-snug text-text-primary sm:text-display">
            A real summary, and an English translation — generated from what was actually said, never assumed.
          </p>
          <div className="mx-auto mt-8 flex max-w-xs items-center justify-center gap-6 text-caption text-text-muted">
            <span className="flex items-center gap-1.5">
              <Icon name="summary" size={14} className="text-accent" /> Executive summary
            </span>
            <span className="flex items-center gap-1.5">
              <Icon name="translate" size={14} className="text-accent" /> Translation
            </span>
          </div>
        </div>
      </section>

      {/* Section 3 — Ask. A command-surface replica (non-functional,
          illustrative) - the same visual language the real Search/Chat
          panels use, so this reads as a preview of the actual product,
          not a generic marketing mock. */}
      <section className="relative z-10 border-t border-border bg-bg px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto grid max-w-5xl grid-cols-1 items-center gap-12 lg:grid-cols-[1fr_1fr]">
          <div className="order-2 lg:order-1">
            <div className="rounded-lg border border-ai-border bg-surface shadow-md">
              <div className="flex items-center gap-2.5 border-b border-border px-4 py-3">
                <span className="font-mono text-body-sm text-ai">›</span>
                <span className="text-body-sm text-text-muted">What did they say about pricing?</span>
              </div>
              <div className="flex flex-col gap-2.5 p-4">
                <div className="h-2 w-4/5 rounded-full bg-ai-muted" />
                <div className="h-2 w-3/5 rounded-full bg-surface-elevated" />
                <div className="mt-1 flex items-center gap-1.5 text-caption text-ai">
                  <Icon name="search" size={11} /> Matched at 12:04
                </div>
              </div>
            </div>
          </div>
          <div className="order-1 lg:order-2">
            <p className="text-label font-semibold uppercase tracking-wide text-ai">03 — Ask</p>
            <h2 className="mt-3 font-display text-display-lg font-semibold leading-tight text-text-primary">
              Semantic search,
              <br />
              grounded answers.
            </h2>
            <p className="mt-5 max-w-md text-body leading-relaxed text-text-secondary">
              Retrieval finds the moment that matches what you mean, not just the words you typed — and Nova
              answers with the real transcript as its evidence, citing where it came from.
            </p>
          </div>
        </div>
      </section>

      {/* Section 4 — Study. Layered/spatial flashcard composition - a
          third distinct rhythm (neither split nor centered-statement). */}
      <section className="relative z-10 border-t border-border bg-bg-secondary px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto flex max-w-5xl flex-col items-center gap-12 lg:flex-row lg:justify-between">
          <div className="max-w-md text-center lg:text-left">
            <p className="text-label font-semibold uppercase tracking-wide text-atmosphere">04 — Study</p>
            <h2 className="mt-3 font-display text-display-lg font-semibold leading-tight text-text-primary">
              Quiz questions and flashcards, drawn from the transcript.
            </h2>
            <p className="mt-5 text-body leading-relaxed text-text-secondary">
              For review and study, not just retrieval — generated once, ready whenever you come back to a video.
            </p>
          </div>
          <div className="relative h-40 w-56 shrink-0">
            <div className="absolute inset-0 translate-x-4 translate-y-3 rotate-3 rounded-lg border border-border bg-surface-elevated shadow-sm" />
            <div className="absolute inset-0 translate-x-2 translate-y-1.5 -rotate-1 rounded-lg border border-border bg-surface-elevated shadow-sm" />
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-lg border border-atmosphere-border bg-surface p-4 text-center shadow-md">
              <Icon name="flashcard" size={20} className="text-atmosphere" />
              <span className="text-caption font-medium text-text-secondary">Question · Answer</span>
            </div>
          </div>
        </div>
      </section>

      {/* Section 5 — Enterprise workflow. A horizontal pipeline of the
          real stages (upload -> pipeline), the most "process" rhythm. */}
      <section className="relative z-10 border-t border-border bg-bg px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto max-w-5xl">
          <p className="text-center text-label font-semibold uppercase tracking-wide text-text-muted">
            The same pipeline, every time
          </p>
          <div className="mt-10 grid grid-cols-2 gap-x-6 gap-y-10 sm:grid-cols-4">
            {[
              { icon: "upload" as const, label: "Upload" },
              { icon: "transcript" as const, label: "Transcribe" },
              { icon: "summary" as const, label: "Understand" },
              { icon: "search" as const, label: "Ready" },
            ].map((step, index) => (
              <div key={step.label} className="relative flex flex-col items-center text-center">
                {index < 3 && (
                  <div
                    className="pointer-events-none absolute left-1/2 top-6 hidden h-px w-full bg-border sm:block"
                    aria-hidden="true"
                  />
                )}
                <span className="relative flex h-12 w-12 items-center justify-center rounded-full border border-border-strong bg-surface text-accent">
                  <Icon name={step.icon} size={18} />
                </span>
                <span className="mt-3 text-body-sm font-medium text-text-primary">{step.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA — full-bleed, minimal, centered - deliberately the
          quietest section on the page after five with real composition. */}
      <section className="relative z-10 border-t border-border bg-bg-secondary px-6 py-24 text-center sm:px-10">
        <p className="font-display text-display-lg font-semibold text-text-primary">
          Bring your own footage.
        </p>
        <p className="mx-auto mt-3 max-w-sm text-body text-text-secondary">
          Free to start — upload a video and see what ReelSense finds in it.
        </p>
        <Link
          href={ROUTES.register}
          className="mt-8 inline-flex items-center rounded-full bg-accent px-6 py-3 text-body font-medium text-accent-on shadow-glow-primary transition-colors duration-fast hover:bg-accent-hover"
        >
          Get started free
        </Link>
      </section>

      <footer className="relative z-10 border-t border-border px-6 py-8 text-center text-caption text-text-muted sm:px-10">
        ReelSense — a video intelligence environment, with Nova inside it.
      </footer>
    </div>
  );
}
