import type { Config } from "tailwindcss";

/**
 * Design tokens for ReelSense.
 *
 * Visual identity: "Daylight Intelligence" — a light-first Cloud/Mist/
 * Ink foundation (not black-as-default) carrying four real hue
 * identities: Cobalt/Indigo primary (navigation, primary actions),
 * Teal signal (AI/live-intelligence states only, same hue family as
 * Nova's own M_Signal material, deepened for contrast on light
 * surfaces), Violet secondary (Study mode identity, same family as
 * Nova's M_Cheek, likewise deepened), and a controlled Warm coral/
 * amber accent reserved for genuine achievement moments. See
 * globals.css for the exact values and the full rationale. All values
 * are also defined as CSS custom properties in globals.css so non-
 * Tailwind contexts (e.g. <video> chrome) can use them too — Tailwind
 * classes here simply reference those variables, so there is one
 * source of truth, not two.
 */
const config: Config = {
  darkMode: "class",
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        "bg-secondary": "rgb(var(--color-bg-secondary) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        "surface-elevated": "rgb(var(--color-surface-elevated) / <alpha-value>)",
        "surface-hover": "rgb(var(--color-surface-hover) / <alpha-value>)",
        "surface-sunken": "rgb(var(--color-surface-sunken) / <alpha-value>)",

        border: {
          DEFAULT: "rgb(var(--color-border) / <alpha-value>)",
          strong: "rgb(var(--color-border-strong) / <alpha-value>)",
        },

        text: {
          primary: "rgb(var(--color-text-primary) / <alpha-value>)",
          secondary: "rgb(var(--color-text-secondary) / <alpha-value>)",
          muted: "rgb(var(--color-text-muted) / <alpha-value>)",
          disabled: "rgb(var(--color-text-disabled) / <alpha-value>)",
        },

        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          hover: "rgb(var(--color-accent-hover) / <alpha-value>)",
          active: "rgb(var(--color-accent-active) / <alpha-value>)",
          muted: "rgb(var(--color-accent) / 0.12)",
          border: "rgb(var(--color-accent) / 0.35)",
          on: "rgb(var(--color-on-accent) / <alpha-value>)",
        },

        // AI accent - Nova, AI-generated content, retrieval/evidence
        // indicators only. Never used for general product chrome
        // (that stays "accent"/copper) - see globals.css for why
        // this exact value.
        ai: {
          DEFAULT: "rgb(var(--color-ai) / <alpha-value>)",
          hover: "rgb(var(--color-ai-hover) / <alpha-value>)",
          muted: "rgb(var(--color-ai) / 0.12)",
          border: "rgb(var(--color-ai) / 0.35)",
          on: "rgb(var(--color-on-ai) / <alpha-value>)",
        },

        // Atmosphere - violet (M_Cheek). A real secondary accent now:
        // the Study mode's identity color (Quiz/Flashcards - a
        // different kind of engagement from Pearl's primary actions
        // or Signal's live AI activity), plus the low-opacity ambient
        // glow (.atmosphere-glow in globals.css) it started as.
        atmosphere: {
          DEFAULT: "rgb(var(--color-atmosphere) / <alpha-value>)",
          hover: "rgb(var(--color-atmosphere-hover) / <alpha-value>)",
          muted: "rgb(var(--color-atmosphere) / 0.14)",
          border: "rgb(var(--color-atmosphere) / 0.35)",
          on: "rgb(var(--color-on-atmosphere) / <alpha-value>)",
        },

        // Warm - a controlled coral/amber accent for a single class of
        // moment: a genuine achievement (e.g. a completed study
        // session), never routine UI or a fourth "brand" color.
        warm: {
          DEFAULT: "rgb(var(--color-warm) / <alpha-value>)",
          hover: "rgb(var(--color-warm-hover) / <alpha-value>)",
          muted: "rgb(var(--color-warm) / 0.14)",
          on: "rgb(var(--color-on-warm) / <alpha-value>)",
        },

        success: {
          DEFAULT: "rgb(var(--color-success) / <alpha-value>)",
          muted: "rgb(var(--color-success) / 0.14)",
        },
        warning: {
          DEFAULT: "rgb(var(--color-warning) / <alpha-value>)",
          muted: "rgb(var(--color-warning) / 0.14)",
        },
        error: {
          DEFAULT: "rgb(var(--color-error) / <alpha-value>)",
          muted: "rgb(var(--color-error) / 0.14)",
        },
        info: {
          DEFAULT: "rgb(var(--color-info) / <alpha-value>)",
          muted: "rgb(var(--color-info) / 0.14)",
        },
      },
      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      fontSize: {
        // Hero-only: oversized, fluid identity typography for the
        // auth/arrival composition. Never used inside the workspace,
        // which stays compact (see the rest of this scale) — per the
        // brand rule "hero typography can be very large, workspace
        // typography must be compact."
        hero: ["clamp(2.75rem, 2vw + 2.25rem, 5rem)", { lineHeight: "0.98", letterSpacing: "-0.03em" }],
        "display-lg": ["2.5rem", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        display: ["1.875rem", { lineHeight: "1.2", letterSpacing: "-0.015em" }],
        "heading-lg": ["1.5rem", { lineHeight: "1.3", letterSpacing: "-0.01em" }],
        heading: ["1.25rem", { lineHeight: "1.35" }],
        "heading-sm": ["1.0625rem", { lineHeight: "1.4" }],
        "body-lg": ["1rem", { lineHeight: "1.65" }],
        body: ["0.9375rem", { lineHeight: "1.6" }],
        "body-sm": ["0.8125rem", { lineHeight: "1.5" }],
        label: ["0.8125rem", { lineHeight: "1.4", letterSpacing: "0.01em" }],
        caption: ["0.75rem", { lineHeight: "1.4" }],
      },
      // A deliberately two-register shape language: controls (buttons,
      // inputs, badges - sm/DEFAULT/md) stay tight and technical; only
      // major media/identity surfaces (xl/2xl - the video canvas,
      // hero panels, Nova's own frame) get a generous, cinematic
      // curve. Not one uniform "rounded-xl everywhere" scale.
      borderRadius: {
        sm: "3px",
        DEFAULT: "5px",
        md: "7px",
        lg: "10px",
        xl: "20px",
        "2xl": "28px",
      },
      // Soft, neutral-tinted shadows (slate, not pure black) - the
      // refined-light-UI convention; pure-black shadows at dark-theme
      // opacities read as harsh smudges on white surfaces.
      boxShadow: {
        sm: "0 1px 2px rgb(15 23 42 / 0.06), 0 1px 1px rgb(15 23 42 / 0.04)",
        md: "0 8px 24px -4px rgb(15 23 42 / 0.10), 0 2px 8px -2px rgb(15 23 42 / 0.06)",
        lg: "0 20px 48px -8px rgb(15 23 42 / 0.14), 0 4px 16px -4px rgb(15 23 42 / 0.08)",
        focus: "0 0 0 2px rgb(var(--color-accent) / 0.45)",
        // Restrained bloom, not a neon border - used sparingly (a
        // hovered AI-marked control, a just-answered chat state).
        "glow-signal": "0 0 24px -6px rgb(var(--color-ai) / 0.4)",
        "glow-secondary": "0 0 28px -8px rgb(var(--color-atmosphere) / 0.35)",
        "glow-primary": "0 0 24px -6px rgb(var(--color-accent) / 0.3)",
      },
      // Motion system: five durations, four easings, used consistently
      // rather than ad hoc per-component values. "spatial"/"hero" are
      // for things moving through real perceived depth (page entrance,
      // workspace mode transitions, Nova) - slower and more deliberate
      // than ordinary UI feedback (fast/base/slow).
      transitionDuration: {
        fast: "120ms",
        base: "180ms",
        slow: "260ms",
        spatial: "420ms",
        hero: "700ms",
      },
      transitionTimingFunction: {
        calm: "cubic-bezier(0.4, 0, 0.2, 1)",
        // standard: general-purpose UI motion (hover, focus, toggles).
        standard: "cubic-bezier(0.4, 0, 0.2, 1)",
        // emphasized: decelerates hard at the end - for something
        // arriving and settling (panels, modals, page content).
        emphasized: "cubic-bezier(0.05, 0.7, 0.1, 1)",
        // spatial: a slower, symmetric ease for things moving through
        // depth (workspace mode switches, Nova camera-adjacent moves).
        spatial: "cubic-bezier(0.65, 0, 0.35, 1)",
        // spring: a restrained overshoot, for a single celebratory
        // moment (success states) - not for routine UI.
        spring: "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
      zIndex: {
        dropdown: "20",
        sticky: "30",
        overlay: "40",
        modal: "50",
        toast: "60",
        tooltip: "70",
      },
      animation: {
        "fade-in": "fade-in 180ms cubic-bezier(0.4,0,0.2,1)",
        "slide-up": "slide-up 220ms cubic-bezier(0.4,0,0.2,1)",
        shimmer: "shimmer 1.8s ease-in-out infinite",
        // A hero/landing-scale entrance - depth (scale+blur) settling
        // in, not just a fade. Reserved for once-per-page-load moments
        // (hero headline, auth panel), never routine UI.
        rise: "rise 700ms cubic-bezier(0.05,0.7,0.1,1) both",
        "mode-enter": "mode-enter 420ms cubic-bezier(0.65,0,0.35,1) both",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-up": {
          from: { opacity: "0", transform: "translateY(6px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        rise: {
          from: { opacity: "0", transform: "translateY(28px) scale(0.98)", filter: "blur(6px)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)", filter: "blur(0)" },
        },
        "mode-enter": {
          from: { opacity: "0", transform: "translateY(10px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
