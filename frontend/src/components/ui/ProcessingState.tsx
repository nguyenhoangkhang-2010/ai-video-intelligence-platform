import { Icon, type IconName } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

interface ProcessingStateProps {
  icon?: IconName;
  title: string;
  description?: string;
  compact?: boolean;
  className?: string;
}

/**
 * A distinct "the pipeline hasn't reached this yet, but it's actually
 * still running" state — deliberately different from EmptyState
 * (which means "the pipeline finished and there is genuinely
 * nothing here"). Every per-artifact workspace panel
 * (Transcript/Summary/Translation/Quiz/Flashcards/Chapters) renders
 * this instead of EmptyState while `video.status` is non-terminal, so
 * a video mid-pipeline never reads as "this will never have a
 * translation" when it's really just not generated yet — see
 * lib/constants.ts::isTerminalVideoStatus and the polling wired into
 * each of those panels' hooks, which is what actually makes this
 * state resolve into real content once the backend catches up rather
 * than requiring a manual page reload.
 */
export function ProcessingState({ icon = "clock", title, description, compact, className }: ProcessingStateProps) {
  return (
    <div
      className={cn(
        "flex animate-fade-in flex-col items-center justify-center text-center",
        compact ? "gap-2 py-8" : "gap-3 py-16",
        className,
      )}
      role="status"
    >
      <div
        className={cn(
          "relative flex items-center justify-center rounded-full bg-ai-muted text-ai",
          compact ? "h-9 w-9" : "h-12 w-12",
        )}
      >
        <span className="absolute inset-0 animate-pulse rounded-full bg-ai/15" aria-hidden="true" />
        <Icon name={icon} size={compact ? 18 : 22} className="relative" />
      </div>
      <div className="max-w-sm">
        <p className={cn("font-medium text-text-primary", compact ? "text-body-sm" : "text-body")}>{title}</p>
        {description && <p className="mt-1 text-body-sm text-text-muted">{description}</p>}
      </div>
    </div>
  );
}
