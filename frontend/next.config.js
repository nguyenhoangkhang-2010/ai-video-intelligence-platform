// The backend origin the browser actually talks to (video streaming,
// every API call, WebSocket-free) - same value the app itself already
// reads via NEXT_PUBLIC_API_URL (see src/lib/constants.ts), so CSP
// stays in sync with wherever the app is actually configured to call
// rather than a hardcoded guess.
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Scoped to what this app genuinely uses, not a copy-pasted generic
// policy - verified live against Landing (Nova hero), the Workspace
// (video playback + Nova + all 9 panels), and Upload (Nova + real
// upload), specifically checking for CSP violation console errors.
//   script-src 'unsafe-inline': Next.js App Router's own hydration
//     bootstrap script is inline; nonce-based CSP would need
//     middleware this app doesn't have.
//   script-src 'unsafe-eval', DEV ONLY: Next's Fast Refresh/HMR
//     runtime (node_modules/@next/react-refresh-utils) genuinely
//     calls eval() to apply hot-reloaded modules - without this, EVERY
//     module load throws a CSP EvalError in dev mode, which is bad
//     enough to prevent the app from ever finishing hydration (found
//     live: this alone was severe enough to look like "Library click
//     doesn't open the workspace" - the whole app was stuck, not just
//     one route). Production's own output never calls eval(), so this
//     is correctly omitted from the production policy rather than
//     accepted as a permanent security trade-off.
//   script-src 'wasm-unsafe-eval', BOTH dev and prod: a separate,
//     narrower grant than 'unsafe-eval' - CSP's dedicated exception for
//     WebAssembly.instantiate()/.compile(), added to the spec precisely
//     so a WASM-using site doesn't need the much broader 'unsafe-eval'
//     (arbitrary string-to-JS eval) just to run it. three-stdlib's
//     Draco/Meshopt geometry decoders (used by useGLTF for nova.glb, on
//     every page Nova appears on - Landing, Library, Upload, Workspace)
//     are WASM. Found live: testing only the DEV server previously hid
//     this - dev mode's 'unsafe-eval' (above) is broad enough to also
//     happen to cover WASM as a side effect, so this gap only showed up
//     once the actual PRODUCTION build (which correctly excludes plain
//     'unsafe-eval') was tested through the real Docker+HTTPS stack:
//     every single page threw an uncaught CompileError instead of
//     rendering Nova. This is exactly why the production target has to
//     be verified directly rather than inferred from dev-mode testing.
//   style-src 'unsafe-inline': this codebase uses real inline
//     `style={{...}}` attributes for computed gradients (Nova's
//     atmosphere glow, per-section tinting) - CSP has no widely
//     supported nonce mechanism for style ATTRIBUTES specifically.
//   worker-src/child-src blob:: three-stdlib's Draco/Meshopt decoders
//     (used by useGLTF for nova.glb) load via blob-URL workers.
//   connect-src/media-src API_ORIGIN: every API call and the video
//     byte stream both come from the backend's own origin, a
//     different origin than the frontend under CSP. connect-src 'self'
//     also covers the dev-mode HMR WebSocket (same origin).
//   No third-party connect-src entry for drei's HDRI: NovaScene now
//     loads the environment map from this app's own /public/assets/hdr
//     (see src/components/3d/NovaScene.tsx) instead of drei's built-in
//     preset="studio", which fetches from a CDN hardcoded into
//     @react-three/drei (node_modules/@react-three/drei/core/
//     useEnvironment.js's CUBEMAP_ROOT) that 301-redirects cross-origin
//     (raw.githack.com -> raw.githubusercontent.com) - found live:
//     allowlisting only the first hop still left the redirect target
//     blocked, so the fetch kept failing on every page load regardless.
//     Self-hosting the asset removes the third-party runtime dependency
//     entirely rather than chasing the redirect chain in CSP.
const isDev = process.env.NODE_ENV !== "production";
const CSP = [
  "default-src 'self'",
  `script-src 'self' 'unsafe-inline' 'wasm-unsafe-eval'${isDev ? " 'unsafe-eval'" : ""}`,
  "style-src 'self' 'unsafe-inline'",
  "img-src 'self' data: blob:",
  "font-src 'self' data:",
  `connect-src 'self' ${API_ORIGIN}`,
  `media-src 'self' ${API_ORIGIN}`,
  "worker-src 'self' blob:",
  "child-src 'self' blob:",
  "frame-ancestors 'none'",
  "base-uri 'self'",
  "form-action 'self'",
].join("; ");

const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Content-Security-Policy", value: CSP },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  eslint: {
    ignoreDuringBuilds: false,
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: SECURITY_HEADERS,
      },
    ];
  },
};

module.exports = nextConfig;
