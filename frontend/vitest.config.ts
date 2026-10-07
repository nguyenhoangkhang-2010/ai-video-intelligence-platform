import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

/**
 * Deliberately separate from next.config.js / the Next.js build
 * pipeline — this only needs to compile plain TS/TSX for jsdom, not
 * run the Next.js dev/build server. Path alias mirrors tsconfig.json
 * exactly (`@/*` -> `src/*`) so tests import components/hooks/
 * services the same way application code does.
 */
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true,
    css: false,
    // e2e/ holds Playwright specs (a different test runner entirely,
    // driven by `npm run test:e2e` / playwright.config.ts) - Vitest's
    // default *.spec.ts glob was picking critical-path.spec.ts up
    // too, failing to collect it (test.describe.serial isn't valid
    // outside Playwright's own runner) and reporting it as a failed
    // suite in `npm test`.
    exclude: ["**/node_modules/**", "**/e2e/**"],
  },
});
