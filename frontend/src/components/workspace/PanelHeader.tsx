import type { ReactNode } from "react";

import { Icon, type IconName } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

interface PanelHeaderProps {
  icon: IconName;
  label: string;
  meta?: ReactNode;
  actions?: ReactNode;
  tone?: "default" | "ai";
  className?: string;
}

/**
 * Shared header for workspace panels (Transcript, Summary,
 * Translation, Search, Chapters) — one consistent way to present
 * "what this panel is + relevant real metadata", instead of each
 * panel inventing its own ad hoc top bar. Typography-led rather than
 * an icon-in-a-colored-box utility bar: the label itself carries the
 * weight, the icon sits inline and quiet as a small mark next to it.
 * `tone="ai"` marks a panel whose content is model-generated/
 * retrieval-driven (Search) with the cyan accent on both.
 */
export function PanelHeader({ icon, label, meta, actions, tone = "default", className }: PanelHeaderProps) {
  return (
    <div
      className={cn(
        "flex shrink-0 flex-wrap items-baseline justify-between gap-3 border-b border-border px-6 py-5 sm:px-8",
        className,
      )}
    >
      <div className="flex items-baseline gap-3">
        <span className="flex items-baseline gap-2 font-display text-heading-sm font-semibold text-text-primary">
          <Icon name={icon} size={17} className={cn("relative top-0.5 shrink-0", tone === "ai" ? "text-ai" : "text-text-muted")} />
          {label}
        </span>
        {meta && <span className="text-caption text-text-muted">{meta}</span>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
