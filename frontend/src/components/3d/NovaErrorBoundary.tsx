"use client";

import { Component, type ReactNode } from "react";

interface NovaErrorBoundaryProps {
  children: ReactNode;
  fallback: ReactNode;
}

interface NovaErrorBoundaryState {
  hasError: boolean;
}

/**
 * GLB loading/WebGL failures must never take the rest of the product
 * down with them - Nova is a supplementary visual layer, not
 * something any workflow depends on. React error boundaries can only
 * be class components; this is intentionally the one class component
 * in the app, scoped to exactly this concern.
 */
export class NovaErrorBoundary extends Component<NovaErrorBoundaryProps, NovaErrorBoundaryState> {
  state: NovaErrorBoundaryState = { hasError: false };

  static getDerivedStateFromError(): NovaErrorBoundaryState {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    if (process.env.NODE_ENV !== "production") {
      // eslint-disable-next-line no-console
      console.error("Nova failed to load:", error);
    }
  }

  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}
