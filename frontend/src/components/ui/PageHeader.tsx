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
 * Top-level route header (Library, Account): a printed index label, a
 * Sora title, and a heavy ink rule underneath - the "case-back
 * engraving" that names the page. No card, no tinted band.
 */
export function PageHeader({ eyebrow, title, description, meta, actions, className }: PageHeaderProps) {
  return (
    <header className={cn("shrink-0 px-6 pt-7 sm:px-10 sm:pt-9", className)}>
      <div className="flex flex-wrap items-end justify-between gap-4 border-b-2 border-text-primary pb-5">
        <div className="min-w-0">
          <p className="index-label text-text-secondary">{eyebrow}</p>
          <h1 className="mt-2 font-display text-display-lg font-semibold leading-none tracking-tight text-text-primary">
            {title}
          </h1>
          {description && <p className="mt-3 max-w-xl text-body-sm text-text-secondary">{description}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {meta}
          {actions}
        </div>
      </div>
    </header>
  );
}
