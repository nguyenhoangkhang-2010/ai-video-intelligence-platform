import "@testing-library/jest-dom/vitest";

// jsdom doesn't implement Element.scrollTo (used by ChatPanel to
// auto-scroll to the latest message) - a no-op stub is enough since
// tests only need the call not to throw, never real scroll behavior.
if (!Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {};
}
