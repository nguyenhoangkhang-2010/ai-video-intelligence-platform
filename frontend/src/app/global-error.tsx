"use client";

import { useEffect } from "react";

/**
 * Catches an error thrown by the root layout itself (fonts/Providers) -
 * the one place App Router requires a component to render its own
 * <html>/<body>, since the real root layout is what crashed. Every
 * other route is covered by a nested error.tsx that keeps the app
 * chrome (TopNav, auth shell) intact instead of replacing the page.
 */
export default function GlobalError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <html lang="en">
      <body style={{ background: "#0a0a0f", color: "#f5f5f7" }}>
        <div
          style={{
            display: "flex",
            height: "100vh",
            width: "100%",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "0.75rem",
            textAlign: "center",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <p style={{ fontSize: "1.25rem", fontWeight: 600 }}>Something went wrong</p>
          <p style={{ fontSize: "0.875rem", color: "#9a9aa5", maxWidth: "28rem" }}>
            ReelSense hit an unexpected error loading the app. Reloading usually fixes it.
          </p>
          <button
            type="button"
            onClick={() => reset()}
            style={{
              marginTop: "0.25rem",
              borderRadius: "0.375rem",
              border: "1px solid #2a2a35",
              padding: "0.5rem 1rem",
              fontSize: "0.875rem",
              color: "#f5f5f7",
              background: "transparent",
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
