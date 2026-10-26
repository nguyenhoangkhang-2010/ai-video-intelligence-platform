import type { ReactNode } from "react";

import { DialRing } from "@/components/dial/DialRing";
import { Icon, type IconName } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  description?: string;
  action?: ReactNode;
  compact?: boolean;
  className?: string;
}

/** Generic "nothing here yet" state — an empty dial, always paired with a specific title. */
export function EmptyState({
  icon = "empty-inbox",
  title,
  description,
  action,
  compact,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex animate-fade-in flex-col items-center justify-center text-center",
        compact ? "gap-2 py-8" : "gap-3 py-16",
        className,
      )}
    >
      <DialRing size={compact ? 44 : 64} ticks={12} majorEvery={3} caseWidth={7}>
        <Icon name={icon} size={compact ? 16 : 20} className="text-text-secondary" />
      </DialRing>
      <div className="max-w-sm">
        <p className={cn("font-display font-semibold text-text-primary", compact ? "text-body-sm" : "text-body-lg")}>
          {title}
        </p>
        {description && <p className="mt-1 text-body-sm text-text-secondary">{description}</p>}
      </div>
      {action}
    </div>
  );
}
