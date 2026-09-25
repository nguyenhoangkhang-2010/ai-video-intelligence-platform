import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Icon, type IconName } from "@/components/ui/Icon";
import type { ApiError } from "@/lib/axios";
import { cn } from "@/lib/utils";

interface ErrorPresentation {
  icon: IconName;
  title: string;
}

/**
 * Maps a resolved HTTP status to a specific icon/title — every error
 * state gets real, useful context instead of a generic "Something
 * went wrong." The backend's own message (see lib/axios.ts::toApiError)
 * fills in the description underneath.
 */
function presentationFor(status: number | null): ErrorPresentation {
  switch (status) {
    case 401:
      return { icon: "lock", title: "Your session has expired" };
    case 403:
      return { icon: "lock", title: "You don't have access to this" };
    case 404:
      return { icon: "file-warning", title: "We couldn't find that" };
    case 409:
      return { icon: "alert", title: "That already exists" };
    case 422:
      return { icon: "file-warning", title: "Some details need fixing" };
    case null:
      return { icon: "wifi-off", title: "Can't reach the server" };
    default:
      if (status >= 500) return { icon: "server-off", title: "The server hit a problem" };
      return { icon: "alert", title: "Something went wrong" };
  }
}

interface ErrorStateProps {
  error: ApiError;
  onRetry?: () => void;
  retryLabel?: string;
  compact?: boolean;
  action?: ReactNode;
  className?: string;
}

export function ErrorState({
  error,
  onRetry,
  retryLabel = "Try again",
  compact,
  action,
  className,
}: ErrorStateProps) {
  const { icon, title } = presentationFor(error.status);

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        compact ? "gap-2 py-8" : "gap-3 py-16",
        className,
      )}
      role="alert"
    >
      <div
        className={cn(
          "flex items-center justify-center rounded-full bg-error-muted text-error",
          compact ? "h-9 w-9" : "h-12 w-12",
        )}
      >
        <Icon name={icon} size={compact ? 18 : 22} />
      </div>
      <div className="max-w-sm">
        <p className={cn("font-medium text-text-primary", compact ? "text-body-sm" : "text-body")}>
          {title}
        </p>
        <p className="mt-1 text-body-sm text-text-muted">{error.message}</p>
      </div>
      {(onRetry || action) && (
        <div className="mt-1 flex items-center gap-2">
          {onRetry && (
            <Button variant="secondary" size="sm" onClick={onRetry}>
              <Icon name="refresh" size={14} />
              {retryLabel}
            </Button>
          )}
          {action}
        </div>
      )}
    </div>
  );
}
