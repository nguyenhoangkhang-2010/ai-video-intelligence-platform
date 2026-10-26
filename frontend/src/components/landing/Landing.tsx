"use client";

import Link from "next/link";
import { useEffect, useRef, useState, type RefObject } from "react";

import { Movement3D } from "@/components/3d/horology/Movement3D";
import { Nova } from "@/components/3d/Nova";
import { DialRing } from "@/components/dial/DialRing";
import { Icon, type IconName } from "@/components/ui/Icon";
import { Wordmark } from "@/components/ui/Logo";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

/**
 * The six layers of the 3D movement, bottom to top, each naming one
 * real stage of what ReelSense does to a video. Order matches the
 * layer indices in MovementImpl.tsx.
 */
const LAYERS: Array<{ no: string; title: string; body: string }> = [
  { no: "01", title: "Ingest", body: "The upload lands in your library and the pipeline starts on its own — no settings, no queue to babysit." },
  { no: "02", title: "Transcribe", body: "Whisper turns every spoken word into a timed transcript you can read, search and cite." },
  { no: "03", title: "Chapter", body: "The video is cut into ordered chapters, each one a mark on the bezel you can jump straight to." },
  { no: "04", title: "Understand", body: "A summary of what was actually said, plus a translation — generated from the transcript, never guessed." },
  { no: "05", title: "Ask", body: "Semantic search finds the moment you mean; Nova answers with the real transcript as evidence." },
  { no: "06", title: "Study", body: "Quiz questions and flashcards drawn from the video, ready whenever you come back to it." },
];

const COMPLICATIONS: Array<{ label: string; icon: IconName; tone: "lume" | "ai" | "atmosphere" | "ink"; progress: number; body: string }> = [
  { label: "Watch", icon: "video", tone: "ink", progress: 0.62, body: "Player, bezel timeline, chapter marks." },
  { label: "Understand", icon: "summary", tone: "lume", progress: 0.4, body: "Transcript, summary, translation." },
  { label: "Ask", icon: "chat", tone: "ai", progress: 0.78, body: "Grounded chat and semantic search." },
  { label: "Study", icon: "quiz", tone: "atmosphere", progress: 0.25, body: "Quizzes and flashcards." },
];

/** 0..1 progress of the window's scroll through `ref`'s element (top hits viewport top → bottom hits viewport bottom). */
function useScrollProgress(ref: RefObject<HTMLElement>) {
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    let frame = 0;
    const update = () => {
      frame = 0;
      const el = ref.current;
      if (!el) return;
      const rect = el.getBoundingClientRect();
      const travel = rect.height - window.innerHeight;
      const value = travel > 0 ? -rect.top / travel : 0;
      setProgress(Math.max(0, Math.min(1, value)));
    };
    const onScroll = () => {
      if (!frame) frame = window.requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, [ref]);
  return progress;
}

/**
 * Mount-while-visible gate for WebGL hosts: each 3D canvas on this page
 * only exists while its section is near the viewport, so the page never
 * holds more than two live WebGL contexts at once.
 */
function useNearViewport<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (typeof IntersectionObserver === "undefined") {
      setNear(true);
      return;
    }
    const observer = new IntersectionObserver(([entry]) => setNear(Boolean(entry?.isIntersecting)), {
      rootMargin: "120px 0px",
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);
  return [ref, near] as const;
}

/**
 * The unauthenticated arrival page, built as a watchmaker's bench:
 * a hero with the assembled movement, then a pinned "exploded view"
 * where scrolling lifts the movement apart layer by layer - each layer
 * naming one real pipeline stage - then the four workspace modes as
 * chronograph sub-dials, and Nova at the end as the one who reads the
 * movement for you. No section shows fabricated AI output.
 */
export function Landing() {
  const explodedRef = useRef<HTMLElement>(null);
  const progress = useScrollProgress(explodedRef);
  const activeLayer = Math.min(LAYERS.length - 1, Math.floor(progress * LAYERS.length));
  const [heroHost, heroNear] = useNearViewport<HTMLDivElement>();
  const [explodedHost, explodedNear] = useNearViewport<HTMLDivElement>();
  const [novaHost, novaNear] = useNearViewport<HTMLDivElement>();

  return (
    <div className="w-full bg-bg text-text-primary">
      <header className="flex items-center justify-between border-b-2 border-text-primary px-6 py-4 sm:px-10">
        <Wordmark />
        <div className="flex items-center gap-2">
          <Link
            href={ROUTES.login}
            className="index-label px-3 py-2 text-text-secondary transition-colors duration-fast hover:text-text-primary"
          >
            Sign in
          </Link>
          <Link
            href={ROUTES.register}
            className="index-label bg-lume px-4 py-2.5 text-lume-on shadow-step-ink transition-[transform,box-shadow] duration-fast hover:bg-lume-hover active:translate-y-[3px] active:shadow-none"
          >
            Get started
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="grid min-h-[calc(100vh-66px)] grid-cols-1 items-center gap-6 px-6 py-12 sm:px-10 lg:grid-cols-[1.05fr_1fr]">
        <div className="max-w-2xl animate-rise">
          <p className="index-label text-text-secondary">Calibre RS-01 · AI video intelligence</p>
          <h1 className="mt-6 font-display text-hero font-semibold tracking-tight">
            Every second
            <br />
            of video,
            <br />
            <span className="relative inline-block">
              measured.
              <span className="absolute -bottom-1 left-0 h-[6px] w-full bg-lume" aria-hidden="true" />
            </span>
          </h1>
          <p className="mt-8 max-w-md text-body-lg text-text-secondary">
            Upload a video and ReelSense transcribes, chapters, summarizes and indexes it — then lets you search,
            ask and study exactly what was said, down to the second.
          </p>
          <div className="mt-10 flex flex-wrap items-center gap-3">
            <Link
              href={ROUTES.register}
              className="inline-flex items-center gap-2 bg-lume px-6 py-3.5 text-body font-semibold text-lume-on shadow-step-ink transition-[transform,box-shadow] duration-fast hover:bg-lume-hover active:translate-y-[3px] active:shadow-none"
            >
              Wind it up — free
              <Icon name="arrow-right" size={16} />
            </Link>
            <Link
              href={ROUTES.login}
              className="inline-flex items-center border border-text-primary/70 px-6 py-3.5 text-body font-medium transition-colors duration-fast hover:bg-surface"
            >
              Sign in
            </Link>
          </div>
          <dl className="mt-14 grid max-w-md grid-cols-3 border-t border-text-primary/30 pt-5">
            {[
              ["9", "workspace modes"],
              ["6", "pipeline stages"],
              ["1 s", "timecode precision"],
            ].map(([value, label]) => (
              <div key={label}>
                <dt className="sr-only">{label}</dt>
                <dd className="font-display text-heading-lg font-semibold">{value}</dd>
                <dd className="index-label mt-1 text-text-muted">{label}</dd>
              </div>
            ))}
          </dl>
        </div>
        <div ref={heroHost} className="relative aspect-square w-full max-w-[640px] justify-self-center">
          {heroNear && <Movement3D explode={0} framing="hero" className="h-full w-full" />}
        </div>
      </section>

      {/* Exploded view - pinned while the movement lifts apart */}
      <section ref={explodedRef} className="relative border-t-2 border-text-primary" style={{ height: "320vh" }}>
        <div className="sticky top-0 grid h-screen grid-cols-1 items-center gap-6 overflow-hidden px-6 sm:px-10 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="relative z-10 max-w-md">
            <p className="index-label text-text-secondary">Exploded view</p>
            <h2 className="mt-3 font-display text-display-lg font-semibold leading-tight">Six layers, one movement.</h2>
            <ol className="mt-8 flex flex-col">
              {LAYERS.map((layer, index) => {
                const active = index === activeLayer;
                return (
                  <li
                    key={layer.no}
                    className={cn(
                      "border-t border-text-primary/25 py-3 transition-colors duration-base",
                      active ? "text-text-primary" : "text-text-disabled",
                    )}
                  >
                    <div className="flex items-baseline gap-4">
                      <span className={cn("font-mono text-body-sm", active && "text-accent")}>{layer.no}</span>
                      <span className="font-display text-heading font-semibold">{layer.title}</span>
                    </div>
                    <p
                      className={cn(
                        "overflow-hidden pl-9 text-body-sm text-text-secondary transition-[max-height,opacity,margin] duration-slow",
                        active ? "mt-1.5 max-h-24 opacity-100" : "max-h-0 opacity-0",
                      )}
                    >
                      {layer.body}
                    </p>
                  </li>
                );
              })}
            </ol>
            <div className="mt-6 h-[3px] w-full bg-text-primary/15" aria-hidden="true">
              <div className="h-full bg-lume" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
          </div>
          <div ref={explodedHost} className="relative h-[70vh] w-full lg:h-[88vh]">
            {explodedNear && (
              <Movement3D explode={Math.min(1, progress * 1.15)} framing="hero" className="h-full w-full" />
            )}
          </div>
        </div>
      </section>

      {/* Complications - the four workspace modes as sub-dials */}
      <section className="border-t-2 border-text-primary bg-surface px-6 py-20 sm:px-10 sm:py-28">
        <div className="mx-auto max-w-6xl">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="index-label text-text-secondary">Complications</p>
              <h2 className="mt-3 max-w-xl font-display text-display-lg font-semibold leading-tight">
                Four sub-dials. Nine ways to read a video.
              </h2>
            </div>
            <p className="max-w-sm text-body-sm text-text-secondary">
              In the workspace, the video sits in the dial and its bezel is the timeline. Each sub-dial opens one
              way of working with what was said.
            </p>
          </div>
          <div className="mt-14 grid grid-cols-2 gap-x-6 gap-y-12 md:grid-cols-4">
            {COMPLICATIONS.map((item) => (
              <div key={item.label} className="flex flex-col items-center text-center">
                <div className="aspect-square w-full max-w-[180px]">
                  <DialRing progress={item.progress} tone={item.tone === "ink" ? "lume" : item.tone} emphasized={item.tone === "ink"}>
                    <div className="flex flex-col items-center gap-1.5">
                      <Icon
                        name={item.icon}
                        size={22}
                        className={cn(
                          item.tone === "ai" && "text-ai",
                          item.tone === "atmosphere" && "text-atmosphere",
                          item.tone === "lume" && "text-accent",
                        )}
                      />
                      <span className="index-label">{item.label}</span>
                    </div>
                  </DialRing>
                </div>
                <p className="mt-4 max-w-[12rem] text-body-sm text-text-secondary">{item.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Nova + final CTA */}
      <section className="border-t-2 border-text-primary px-6 py-20 sm:px-10 sm:py-24">
        <div className="mx-auto grid max-w-5xl grid-cols-1 items-center gap-10 md:grid-cols-[auto_1fr]">
          <div ref={novaHost} className="relative mx-auto h-56 w-56 rounded-full border-[6px] border-case bg-surface-sunken">
            {novaNear && <Nova state="idle" mode="ambient" className="h-full w-full" />}
          </div>
          <div>
            <p className="index-label text-ai">Nova</p>
            <p className="mt-3 font-display text-display font-semibold leading-snug">
              The watchmaker who reads the movement for you — answering from the transcript, citing the second it
              came from.
            </p>
            <Link
              href={ROUTES.register}
              className="mt-8 inline-flex items-center gap-2 bg-lume px-6 py-3.5 text-body font-semibold text-lume-on shadow-step-ink transition-[transform,box-shadow] duration-fast hover:bg-lume-hover active:translate-y-[3px] active:shadow-none"
            >
              Bring your own footage
              <Icon name="arrow-right" size={16} />
            </Link>
          </div>
        </div>
      </section>

      <footer className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-text-primary px-6 py-6 sm:px-10">
        <span className="index-label text-text-secondary">ReelSense · Calibre RS-01</span>
        <span className="index-label text-text-muted">A video intelligence workspace, with Nova inside it</span>
      </footer>
    </div>
  );
}
