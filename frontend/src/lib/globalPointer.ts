/**
 * A single, page-wide normalized pointer position — not React state
 * (a re-render on every pixel of mouse movement would defeat the
 * point). Used by the ambient Nova instance so its look-layer can
 * react to the cursor anywhere on screen, not only while the cursor
 * sits over Nova's own small canvas (R3F's built-in `pointer` is
 * canvas-relative). One `pointermove` listener is attached lazily,
 * once, regardless of how many times `ensureGlobalPointerTracking` is
 * called.
 */

export interface GlobalPointer {
  x: number;
  y: number;
}

const globalPointer: GlobalPointer = { x: 0, y: 0 };
let attached = false;
let pointerActive = false;

export function getGlobalPointer(): GlobalPointer {
  return globalPointer;
}

/** False once the cursor has left the browser window entirely - lets a look-at layer smoothly decay back to a resting gaze instead of holding a stale offset. */
export function isPointerActive(): boolean {
  return pointerActive;
}

export function ensureGlobalPointerTracking(): void {
  if (attached || typeof window === "undefined") return;
  attached = true;

  window.addEventListener(
    "pointermove",
    (event) => {
      pointerActive = true;
      globalPointer.x = (event.clientX / window.innerWidth) * 2 - 1;
      globalPointer.y = -((event.clientY / window.innerHeight) * 2 - 1);
    },
    { passive: true },
  );

  // `relatedTarget === null` on a document-level mouseout means the
  // cursor left the browser window/tab, not just moved between two
  // elements inside it - the standard cross-browser signal for this.
  document.addEventListener(
    "mouseout",
    (event) => {
      if (event.relatedTarget === null) pointerActive = false;
    },
    { passive: true },
  );
}
