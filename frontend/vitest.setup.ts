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
