import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement Element.scrollTo (used by ChatPanel to
// auto-scroll to the latest message) - a no-op stub is enough since
// tests only need the call not to throw, never real scroll behavior.
if (!Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {};
}

// jsdom also doesn't implement ResizeObserver, which @react-three/
// fiber's <Canvas> (via react-use-measure) requires just to mount -
// any panel that renders a Button3D/GLB-backed control (ChatPanel,
// SearchPanel) needs this stub or Canvas throws during render and
// crashes the whole test, regardless of what the test actually
// asserts. A no-op is enough since tests never depend on real resize
// callbacks firing.
if (typeof ResizeObserver === "undefined") {
  class ResizeObserverStub {
    observe() {}
    unobserve() {}
    disconnect() {}
  }
  globalThis.ResizeObserver = ResizeObserverStub;
}

// jsdom doesn't implement window.matchMedia (used by useReducedMotion
// to read prefers-reduced-motion) - any component under its root,
// including WorkspaceNav, throws on mount without this stub. Always
// reports "no preference" (matches: false), which is enough since
// tests only need mounting not to crash, never real media-query
// change notifications.
if (typeof window !== "undefined" && !window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }) as MediaQueryList;
}
