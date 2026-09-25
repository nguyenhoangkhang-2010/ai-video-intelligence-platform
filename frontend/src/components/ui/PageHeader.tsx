import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description?: string;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}

/**
 * Editorial page header shared by top-level routes (Library, Account).
 * Replaces the old `h-14 border-b flex items-center justify-between`
 * pattern that made every page look like the same admin-panel
 * template — this gives each page a title with real hierarchy (an
 * eyebrow label above a display-weight heading) instead of a single
 * flat heading-sm line.
 */
export function PageHeader({ eyebrow, title, description, meta, actions, className }: PageHeaderProps) {
  return (
    <header className={cn("shrink-0 border-b border-border px-6 pb-5 pt-6 sm:px-8 sm:pt-7", className)}>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-label font-medium uppercase tracking-[0.14em] text-text-muted">{eyebrow}</p>
          <h1 className="mt-1 font-display text-display font-semibold leading-tight text-text-primary">
            {title}
          </h1>
          {description && <p className="mt-1.5 max-w-xl text-body-sm text-text-secondary">{description}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {meta}
          {actions}
        </div>
      </div>
    </header>
  );
}
