"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";

import type { NovaState } from "@/components/3d/novaClips";

interface NovaAttentionValue {
  /** The single, product-wide Nova entity's current semantic state. */
  state: NovaState;
  /**
   * Drive that state from anywhere in the app. With `holdMs`, it's a
   * transient pulse that auto-reverts to "idle" (a hover acknowledgement,
   * a short "found it"). Without `holdMs`, it's sustained — the caller
   * owns clearing it (e.g. ChatPanel calls notice("thinking") while a
   * request is in flight, of unknown duration, then notice("success", 1400)
   * once it resolves).
   */
  notice: (state: NovaState, holdMs?: number) => void;
}

const NovaAttentionContext = createContext<NovaAttentionValue | null>(null);

/**
 * Backs the single global Nova instance (see NovaAmbient) so any
 * AI-relevant interaction anywhere in the product — hovering an AI
 * nav item, sending a chat message, running a semantic search — can
 * make the same living entity react, instead of each screen owning an
 * isolated, disconnected Nova of its own.
 */
export function NovaAttentionProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<NovaState>("idle");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const notice = useCallback((next: NovaState, holdMs?: number) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    setState(next);
    if (typeof holdMs === "number") {
      timeoutRef.current = setTimeout(() => setState("idle"), holdMs);
    }
  }, []);

  const value = useMemo<NovaAttentionValue>(() => ({ state, notice }), [state, notice]);

  return <NovaAttentionContext.Provider value={value}>{children}</NovaAttentionContext.Provider>;
}

export function useNovaAttention(): NovaAttentionValue {
  const context = useContext(NovaAttentionContext);
  if (!context) {
    throw new Error("useNovaAttention must be used within a NovaAttentionProvider");
  }
  return context;
}
