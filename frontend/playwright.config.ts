import { defineConfig } from "@playwright/test";

/**
 * One deliberate E2E suite (see e2e/critical-path.spec.ts), separate
 * from Vitest's unit/component tests - this drives a real browser
 * against the real dev server (real auth, real media-token flow,
 * real HTTP streaming) rather than jsdom. Not wired into the fast CI
 * gate (tests.yml/ci.yml): it needs a real Postgres-backed backend
 * reachable at NEXT_PUBLIC_API_URL, which CI doesn't provision - see
 * docs/testing/e2e.md for how to run it locally and why.
 */
export default defineConfig({
  testDir: "./e2e",
  // Generous: Next.js dev mode JIT-compiles each route (including the
  // video workspace's 3D/react-three-fiber client components) on
  // first real navigation, which is genuinely slow the first time -
  // not something to paper over with a shorter, flakier timeout.
  timeout: 90_000,
  fullyParallel: false,
  // This suite navigates a real, uncached Next.js dev server while
  // Docker/Ollama (the real backend this test also exercises) run
  // concurrently on the same host - observed flaky under that real
  // resource contention, not due to a bug in the test logic itself
  // (afterAll's cleanup is written to be resilient to a flaky run -
  // see its own comment). One retry absorbs that, same as most real
  // E2E suites running against a live dev server.
  retries: 1,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "off",
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
