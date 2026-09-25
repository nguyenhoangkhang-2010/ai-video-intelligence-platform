import { forwardRef, useId, useState, type InputHTMLAttributes } from "react";

import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string | null;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, id, className, type, ...props }, ref) => {
    const generatedId = useId();
    const inputId = id ?? generatedId;
    const [revealed, setRevealed] = useState(false);
    const isPassword = type === "password";
    const resolvedType = isPassword && revealed ? "text" : type;

    return (
      <div className="flex flex-col gap-1.5">
        {label && (
          <label htmlFor={inputId} className="text-label font-medium text-text-secondary">
            {label}
          </label>
        )}
        {/*
          Focus is a composed shift (surface lightens to white, a soft
          cobalt ring appears around the whole control), not a bare
          border-color swap - the wrapper carries the ring via
          `focus-within` so it also encloses the password-reveal
          button, and the native `:focus-visible` outline is suppressed
          here specifically (kept everywhere else in the app) since
          this treatment already gives keyboard focus a clearly visible,
          more considered signal than the generic outline would add on
          top of it.
        */}
        <div
          className={cn(
            "relative rounded transition-shadow duration-fast ease-calm",
            "focus-within:shadow-[0_0_0_3px_rgb(var(--color-accent)/0.16)]",
          )}
        >
          <input
            ref={ref}
            id={inputId}
            type={resolvedType}
            aria-invalid={Boolean(error)}
            aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined}
            className={cn(
              "h-10 w-full rounded border bg-surface-sunken px-3 text-body text-text-primary placeholder:text-text-muted",
              "transition-[background-color,border-color] duration-fast ease-calm",
              "focus:outline-none focus:bg-surface",
              error ? "border-error" : "border-border-strong hover:border-text-muted focus:border-accent",
              isPassword && "pr-10",
              className,
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setRevealed((value) => !value)}
              className="absolute right-2.5 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
              aria-label={revealed ? "Hide password" : "Show password"}
              tabIndex={-1}
            >
              <Icon name={revealed ? "eye-off" : "eye"} size={17} />
            </button>
          )}
        </div>
        {error && (
          <p id={`${inputId}-error`} className="flex items-center gap-1 text-caption text-error">
            <Icon name="alert" size={13} />
            {error}
          </p>
        )}
        {!error && hint && (
          <p id={`${inputId}-hint`} className="text-caption text-text-muted">
            {hint}
          </p>
        )}
      </div>
    );
  },
);
Input.displayName = "Input";
