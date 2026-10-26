import { forwardRef, type ButtonHTMLAttributes } from "react";

import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/utils";

// Six variants, each earning its place rather than padding a count:
// primary/secondary/danger/ai already existed; "quiet" formalizes a
// pattern that was already scattered across panels as raw
// `text-accent hover:text-accent-hover` JSX (Overview's "Read the full
// brief →", Chapters' "Open narrative map →", etc.) - the most
// de-emphasized action, text-only, no fill or border, for an inline
// link-weight action next to prose; "ghost" stays the icon-toolbar
// weight (a hover surface, no text color shift needed) - the two are
// visually and semantically distinct, not duplicates.
type Variant = "primary" | "secondary" | "quiet" | "ghost" | "danger" | "ai";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  isLoading?: boolean;
  fullWidth?: boolean;
}

// Raised variants (primary/ai) sit on a hard 3px "machined" step
// (shadow-step - a solid offset, never a blur) and press down onto it
// on :active, like a real pusher on a watch case. Bordered variants
// stay flat; quiet/ghost stay motion-free.
const variantClasses: Record<Variant, string> = {
  primary:
    "bg-lume text-lume-on shadow-step-ink hover:bg-lume-hover active:translate-y-[3px] active:shadow-none disabled:bg-lume/50 disabled:shadow-none",
  secondary:
    "bg-surface-elevated text-text-primary border border-text-primary/70 hover:bg-surface-hover active:bg-surface-sunken disabled:opacity-50",
  quiet:
    "bg-transparent text-accent underline-offset-4 hover:underline disabled:text-text-disabled disabled:no-underline",
  ghost: "bg-transparent text-text-secondary hover:bg-surface-hover hover:text-text-primary",
  danger: "bg-error text-white hover:bg-error/90 active:bg-error/80 disabled:opacity-60",
  // AI-driven actions only (e.g. submitting a semantic search) - petrol,
  // the same colour as Nova/evidence, never general product actions.
  ai: "bg-ai text-ai-on shadow-step-ink hover:bg-ai-hover active:translate-y-[3px] active:shadow-none disabled:bg-ai/50 disabled:shadow-none",
};

const sizeClasses: Record<Size, string> = {
  sm: "h-8 px-3 text-body-sm gap-1.5",
  md: "h-9 px-4 text-body gap-2",
  lg: "h-11 px-5 text-body-lg gap-2",
};

// Quiet has no fill/border to carry the control shape, so it needs
// tighter, text-like padding rather than the button-sized boxes above.
const quietSizeClasses: Record<Size, string> = {
  sm: "h-auto px-0 py-0 text-caption gap-1",
  md: "h-auto px-0 py-0 text-body-sm gap-1.5",
  lg: "h-auto px-0 py-0 text-body gap-1.5",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    { variant = "primary", size = "md", isLoading, fullWidth, disabled, className, children, ...props },
    ref,
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center rounded font-medium tracking-[0.01em] transition-[background-color,border-color,box-shadow,transform,color,opacity] duration-fast ease-calm",
          "disabled:cursor-not-allowed",
          "focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-2",
          variantClasses[variant],
          variant === "quiet" ? quietSizeClasses[size] : sizeClasses[size],
          fullWidth && "w-full",
          className,
        )}
        {...props}
      >
        {isLoading && <Spinner size={16} className="text-current" />}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";
