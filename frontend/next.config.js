// The backend origin the browser actually talks to (video streaming,
// every API call, WebSocket-free) - same value the app itself already
// reads via NEXT_PUBLIC_API_URL (see src/lib/constants.ts), so CSP
// stays in sync with wherever the app is actually configured to call
// rather than a hardcoded guess.
const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

// Scoped to what this app genuinely uses, not a copy-pasted generic
// policy - verified live against Landing (Nova hero), the Workspace
// (video playback + Nova + all 9 panels), and Upload (Nova + real
// upload) after adding this, specifically checking for CSP violation
// console errors.
//   script-src 'unsafe-inline': Next.js App Router's own hydration
//     bootstrap script is inline; nonce-based CSP would need
//     middleware this app doesn't have.
//   style-src 'unsafe-inline': this codebase uses real inline
//     `style={{...}}` attributes for computed gradients (Nova's
//     atmosphere glow, per-section tinting) - CSP has no widely
//     supported nonce mechanism for style ATTRIBUTES specifically.
//   worker-src/child-src blob:: three-stdlib's Draco/Meshopt decoders
//     (used by useGLTF for nova.glb) load via blob-URL workers.
//   connect-src/media-src API_ORIGIN: every API call and the video
//     byte stream both come from the backend's own origin, a
//     different origin than the frontend under CSP.
const CSP = [
  "default-src 'self'",
  "script-src 'self' 'unsafe-inline'",
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
