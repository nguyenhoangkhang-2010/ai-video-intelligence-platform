"use client";

import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { ProcessingState } from "@/components/ui/ProcessingState";
import { Skeleton } from "@/components/ui/Spinner";
import { PanelHeader } from "@/components/workspace/PanelHeader";
import { useSummaries } from "@/hooks/useSummary";
import { toApiError } from "@/lib/axios";
import { isTerminalVideoStatus } from "@/lib/constants";
import { formatDate } from "@/lib/utils";
import type { VideoStatus } from "@/types/video";

/** A summary line rendered as a bullet if it already starts with a list marker in the source text. */
function isBulletLine(line: string): boolean {
  return /^[-*•]\s+/.test(line);
}

type LineGroup = { type: "list" | "paragraph"; lines: string[] };

function groupLines(lines: string[]): LineGroup[] {
  const groups: LineGroup[] = [];
  for (const line of lines) {
    const type = isBulletLine(line) ? "list" : "paragraph";
    const last = groups[groups.length - 1];
    if (last && last.type === type) {
      last.lines.push(line);
    } else {
      groups.push({ type, lines: [line] });
    }
  }
  return groups;
}

/**
 * Labels each real group by its actual position/shape in the content
 * - never a fixed four-section template imposed on text that doesn't
 * have that structure. The first paragraph reads as the executive
 * summary, the first bullet list as key ideas, a second bullet list
 * (if the model produced one) as important moments, and any prose
 * after a list as the conclusion. A summary with only one paragraph
 * gets one label; nothing is invented to fill a template.
 */
function labelFor(group: LineGroup, index: number, groups: LineGroup[]): string | null {
  if (group.type === "paragraph") return index === 0 ? "Executive summary" : "Conclusion";
  const isFirstList = !groups.slice(0, index).some((candidate) => candidate.type === "list");
  return isFirstList ? "Key ideas" : "Important moments";
}

export function SummaryPanel({ videoId, videoStatus }: { videoId: number; videoStatus: VideoStatus }) {
  const summaries = useSummaries(videoId, videoStatus);

  if (summaries.isLoading) {
    return (
      <div className="flex flex-col gap-3 p-5">
        <Skeleton className="h-4 w-1/3" />
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-full" />
        ))}
      </div>
    );
  }

  if (summaries.isError) {
    return <ErrorState error={toApiError(summaries.error)} onRetry={() => summaries.refetch()} compact />;
  }

  const summary = summaries.data?.[0];

  if (!summary) {
    if (!isTerminalVideoStatus(videoStatus)) {
      return (
        <ProcessingState
          icon="summary"
          title="Summary is being generated…"
          description="This updates automatically the moment it's ready — no need to refresh."
        />
      );
    }
    return (
      <EmptyState
        icon="summary"
        title="No summary available"
        description="Processing finished without producing a summary for this video."
      />
    );
  }

  const lines = summary.content.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const groups = groupLines(lines);

  return (
    <div className="flex h-full flex-col">
      <PanelHeader
        icon="summary"
        label="AI Video Report"
        meta={
          <span className="flex items-center gap-2">
            <span>{summary.model_name}</span>
            <span aria-hidden="true">·</span>
            <span>{formatDate(summary.created_at)}</span>
          </span>
        }
      />
      <div className="flex-1 overflow-y-auto p-6 sm:p-8">
        <div className="mx-auto flex max-w-[66ch] flex-col gap-8">
          {groups.map((group, index) => {
            const label = labelFor(group, index, groups);
            const isLead = index === 0 && group.type === "paragraph";
            return (
              <section key={index}>
                {label && (
                  <p className="mb-3 text-label font-semibold uppercase tracking-[0.12em] text-atmosphere">{label}</p>
                )}
                {group.type === "list" ? (
                  <ul className="flex flex-col gap-3">
                    {group.lines.map((line, lineIndex) => (
                      <li key={lineIndex} className="flex gap-3 text-body-lg leading-relaxed text-text-secondary">
                        <span className="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-atmosphere" aria-hidden="true" />
                        <span>{line.replace(/^[-*•]\s+/, "")}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="flex flex-col gap-3">
                    {group.lines.map((line, lineIndex) => (
                      <p
                        key={lineIndex}
                        className={
                          isLead
                            ? "text-heading font-medium leading-relaxed text-text-primary"
                            : "text-body-lg leading-relaxed text-text-secondary"
                        }
                      >
                        {line}
                      </p>
                    ))}
                  </div>
                )}
              </section>
            );
          })}
        </div>
      </div>
    </div>
  );
}
