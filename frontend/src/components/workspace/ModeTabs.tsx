"use client";

import type { KeyboardEvent } from "react";

import { Icon } from "@/components/ui/Icon";
import { WORKSPACE_SECTION_GROUPS, WORKSPACE_SECTIONS, type WorkspaceSection } from "@/components/workspace/sections";
import { cn } from "@/lib/utils";

/**
 * Left/Right (and Home/End) move focus to the adjacent mode and
 * activate it immediately - the WAI-ARIA "automatic activation" tabs
 * pattern, on plain buttons.
 */
function handleArrowKey(event: KeyboardEvent<HTMLButtonElement>) {
  const key = event.key;
  if (key !== "ArrowLeft" && key !== "ArrowRight" && key !== "Home" && key !== "End") return;
  event.preventDefault();
  const row = event.currentTarget.closest("[data-mode-tabs]");
  if (!row) return;
  const buttons = Array.from(row.querySelectorAll<HTMLButtonElement>("button"));
  const index = buttons.indexOf(event.currentTarget);
  if (index === -1) return;
  let next: number;
  if (key === "Home") next = 0;
  else if (key === "End") next = buttons.length - 1;
  else if (key === "ArrowRight") next = (index + 1) % buttons.length;
  else next = (index - 1 + buttons.length) % buttons.length;
  buttons[next]?.focus();
  buttons[next]?.click();
}

function activeTone(tone: "ai" | "atmosphere" | undefined) {
  if (tone === "ai") return "bg-ai";
  if (tone === "atmosphere") return "bg-atmosphere";
  return "bg-lume";
}

/**
 * All nine modes as engraved tabs across the top of the content panel,
 * grouped under their sub-dial name (Watch / Understand / Ask / Study)
 * so every mode is always one click away - the sub-dials and crown are
 * shortcuts, never the only way in. Groups wrap onto a second line on
 * narrow panels instead of scrolling out of sight. Each tab carries its
 * global index (01-09) so the crown's step order is legible.
 */
export function ModeTabs({
  active,
  onSelect,
}: {
  active: WorkspaceSection;
  onSelect: (id: WorkspaceSection) => void;
}) {
  return (
    <div data-mode-tabs className="flex flex-wrap items-stretch">
      {WORKSPACE_SECTION_GROUPS.map((group) => {
        const groupActive = group.ids.includes(active);
        return (
          <div key={group.label} className="flex items-stretch border-r border-text-primary/15 last:border-r-0">
            <span
              className={cn(
                "index-label flex shrink-0 items-center pl-3 pr-1",
                groupActive ? "text-text-primary" : "text-text-muted",
              )}
            >
              {group.label}
            </span>
            {group.ids.map((id) => {
              const section = WORKSPACE_SECTIONS.find((candidate) => candidate.id === id);
              if (!section) return null;
              const number = WORKSPACE_SECTIONS.indexOf(section) + 1;
              const isActive = id === active;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => onSelect(id)}
                  onKeyDown={handleArrowKey}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "relative flex shrink-0 items-center gap-1.5 px-2.5 py-2.5 text-body-sm font-medium transition-colors duration-fast",
                    isActive ? "text-text-primary" : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
                  )}
                >
                  <span className="font-mono text-[11px] text-text-muted" aria-hidden="true">
                    {String(number).padStart(2, "0")}
                  </span>
                  <Icon name={section.icon} size={14} className="shrink-0" />
                  <span className="whitespace-nowrap">{section.label}</span>
                  {isActive && (
                    <span className={cn("absolute inset-x-2 bottom-0 h-[3px]", activeTone(section.tone))} aria-hidden="true" />
                  )}
                </button>
              );
            })}
          </div>
        );
      })}
    </div>
  );
}
