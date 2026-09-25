"use client";

import { usePathname } from "next/navigation";
import { useEffect } from "react";

import { Nova } from "@/components/3d/Nova";
import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { ensureGlobalPointerTracking, getGlobalPointer } from "@/lib/globalPointer";

// Every route below already mounts its own dedicated <Nova> instance
// (see (auth)/layout.tsx, Landing.tsx, library/upload/page.tsx, and
// the embedded workspace instance on /videos/[id]) - the ambient
// instance must stay off everywhere one of those already exists.
// This isn't just a visual/z-index concern: useGLTF caches and shares
// ONE scene graph across every <Nova> consumer, so two concurrently
// mounted instances end up with two independent AnimationMixers
// driving the literal same Head/Eye_L/Eye_R bone objects every frame,
// each overwriting the other's result - that fight is what actually
// produced Nova's "spinning" bug (see NovaModel.tsx, which now also
// clones the scene per instance as a second, structural line of
// defense against this same class of collision).
const SUPPRESSED_PREFIXES = ["/login", "/register", "/videos/", "/library/upload"];
// Matched exactly, never as a prefix - "/".startsWith would otherwise
// match every route in the app and suppress Nova everywhere.
const SUPPRESSED_EXACT = ["/"];

/**
 * The one, page-wide Nova entity. Mounted once at the true root layout
 * so it survives navigation across the whole authenticated app - not
 * a widget re-created per screen. It watches the cursor anywhere on
 * the viewport (lib/globalPointer.ts) and reacts to whatever the
 * shared NovaAttentionContext says is happening (an AI hover
 * elsewhere on the page, a chat request in flight, a search
 * resolving) - see NovaAttentionContext.tsx for who drives it.
 */
export function NovaAmbient() {
  const pathname = usePathname();
  const { state } = useNovaAttention();

  useEffect(() => {
    ensureGlobalPointerTracking();
  }, []);

  if (pathname && (SUPPRESSED_EXACT.includes(pathname) || SUPPRESSED_PREFIXES.some((route) => pathname.startsWith(route)))) {
    return null;
  }

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-tooltip">
      <div className="relative h-14 w-14 rounded-full bg-surface/80 shadow-lg ring-1 ring-black/[0.06] backdrop-blur-sm">
        <Nova state={state} className="h-full w-full" externalPointer={getGlobalPointer()} />
      </div>
    </div>
  );
}
