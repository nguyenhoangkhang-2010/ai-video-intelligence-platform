"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Nova } from "@/components/3d/Nova";
import { DialRing } from "@/components/dial/DialRing";
import { Wordmark } from "@/components/ui/Logo";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/lib/constants";

/**
 * The sign-in bench: on wide screens the form sits inside a large
 * printed watch dial (the bezel ring is pure SVG, the form is ordinary
 * HTML centred in it), with Nova in a porthole beside the headline.
 * Nova's state is the shared, product-wide NovaAttentionContext - this
 * layout fires the one-time arrival "greeting", and LoginPage/
 * RegisterPage drive it from there (focus/submit/success).
 *
 * Mirrors RootPage's own isAuthenticated redirect: an already-signed-
 * in visitor who lands on /login or /register directly (a stale
 * bookmark, browser back, a shared link) is sent on to their library
 * instead of being shown the form again - the same asymmetry
 * RequireAuth already enforces in the other direction for every
 * protected route.
 */
export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const { state, notice } = useNovaAttention();
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    router.replace(ROUTES.library);
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    notice("greeting");
    // Fire once on arrival only - the gesture itself is one-shot and
    // the mixer crossfades back to Idle_Breathe on its own when it
    // finishes (see NovaModel.tsx), independent of this context value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (isLoading || isAuthenticated) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-bg">
        <Spinner size={24} />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full flex-col bg-bg">
      <header className="flex items-center justify-between border-b-2 border-text-primary px-6 py-4 sm:px-10">
        <Wordmark />
        <span className="index-label hidden text-text-secondary sm:inline">Calibre RS-01</span>
      </header>

      <div className="flex flex-1 flex-col items-center justify-center gap-12 px-6 py-10 sm:px-10 lg:flex-row lg:justify-between lg:gap-10 xl:px-20">
        <div className="max-w-lg animate-rise">
          <p className="index-label text-text-secondary">AI video intelligence</p>
          <p className="mt-4 font-display text-hero font-semibold tracking-tight text-text-primary">
            Set the
            <br />
            <span className="relative inline-block">
              time.
              <span className="absolute -bottom-1 left-0 h-[6px] w-full bg-lume" aria-hidden="true" />
            </span>
          </p>
          <p className="mt-6 max-w-sm text-body text-text-secondary">
            Transcripts, chapters, summaries and grounded answers — generated from your footage, timed to the
            second.
          </p>
          <div className="mt-10 flex items-center gap-5">
            <div className="relative h-28 w-28 shrink-0 rounded-full border-[5px] border-case bg-surface-sunken">
              <Nova state={state} mode="ambient" className="h-full w-full" />
            </div>
            <p className="index-label max-w-[12rem] leading-relaxed text-text-secondary">
              Nova watches the form with you
            </p>
          </div>
        </div>

        <div className="relative w-full max-w-[380px] animate-rise lg:aspect-square lg:w-[600px] lg:max-w-none">
          <div className="pointer-events-none absolute inset-0 hidden lg:block" aria-hidden="true">
            <DialRing ticks={60} caseWidth={4} />
          </div>
          <div className="relative flex h-full w-full items-center justify-center">
            <div className="w-full border border-text-primary/60 bg-surface-elevated p-7 shadow-step-ink sm:p-8 lg:w-[330px] lg:border-0 lg:bg-transparent lg:p-0 lg:shadow-none">
              {children}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
