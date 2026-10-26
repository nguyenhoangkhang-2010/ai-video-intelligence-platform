"use client";

import { useEffect, useState } from "react";

/**
 * Tracks `prefers-reduced-motion`, live (not just at mount) - used by
 * the Nova 3D system and anywhere else JS-driven motion (not plain
 * CSS, which globals.css already handles globally) needs to check
 * the same preference.
 */
export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(query.matches);

    const handleChange = (event: MediaQueryListEvent) => setReduced(event.matches);
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);

  return reduced;
}
