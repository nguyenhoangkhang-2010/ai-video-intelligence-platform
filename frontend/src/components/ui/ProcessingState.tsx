import { DialRing } from "@/components/dial/DialRing";
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
 * (which means "the pipeline finished and there is genuinely nothing
 * here"). Every per-artifact workspace panel renders this instead of
 * EmptyState while `video.status` is non-terminal, so a video
 * mid-pipeline never reads as "this will never have a translation"
 * when it's really just not generated yet — see
 * lib/constants.ts::isTerminalVideoStatus and the polling wired into
 * each of those panels' hooks.
 *
 * Drawn as a dial whose petrol seconds hand is still sweeping: the
 * movement is running, the result just isn't out yet.
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
      <DialRing size={compact ? 44 : 64} ticks={12} majorEvery={3} caseWidth={7} emphasized>
        <span className="absolute inset-0 animate-sweep" style={{ animationDuration: "4s" }} aria-hidden="true">
          <span className="absolute left-1/2 top-[14%] h-[36%] w-[2px] -translate-x-1/2 bg-ai" />
        </span>
        <Icon name={icon} size={compact ? 14 : 18} className="relative text-ai" />
      </DialRing>
      <div className="max-w-sm">
        <p className={cn("font-display font-semibold text-text-primary", compact ? "text-body-sm" : "text-body-lg")}>
          {title}
        </p>
        {description && <p className="mt-1 text-body-sm text-text-secondary">{description}</p>}
      </div>
    </div>
  );
}
