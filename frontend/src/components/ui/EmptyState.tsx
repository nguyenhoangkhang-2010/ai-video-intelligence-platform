import type { ReactNode } from "react";

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

/** Generic "nothing here yet" state — always paired with a specific title, never a bare icon. */
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
      <div
        className={cn(
          "flex items-center justify-center rounded-full bg-surface-elevated text-text-muted",
          compact ? "h-9 w-9" : "h-12 w-12",
        )}
      >
        <Icon name={icon} size={compact ? 18 : 22} />
      </div>
      <div className="max-w-sm">
        <p className={cn("font-medium text-text-primary", compact ? "text-body-sm" : "text-body")}>
          {title}
        </p>
        {description && (
          <p className="mt-1 text-body-sm text-text-muted">{description}</p>
        )}
      </div>
      {action}
    </div>
  );
}
