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
  },
});
