"use client";

import { useEffect, useState, type KeyboardEvent } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Icon } from "@/components/ui/Icon";
import { WORKSPACE_SECTION_GROUPS, WORKSPACE_SECTIONS, type WorkspaceSection } from "@/components/workspace/sections";
import { cn } from "@/lib/utils";

interface WorkspaceNavProps {
  active: WorkspaceSection;
  onSelect: (section: WorkspaceSection) => void;
  /**
   * True once the active panel has been scrolled - collapses the two
   * row disclosure below into one thin, always-legible line instead of
   * eating vertical space the whole time a person is reading content.
   * Driven by the page (it owns the scrollable panel container).
   */
  compact?: boolean;
  className?: string;
}

function toneClasses(tone: "ai" | "atmosphere" | undefined, isActive: boolean) {
  if (!isActive) return "text-text-secondary hover:text-text-primary";
  if (tone === "ai") return "text-ai";
  if (tone === "atmosphere") return "text-atmosphere";
  return "text-text-primary";
}

function underlineClasses(tone: "ai" | "atmosphere" | undefined) {
  if (tone === "ai") return "bg-ai";
  if (tone === "atmosphere") return "bg-atmosphere";
  return "bg-accent";
}

// A restrained "elevated surface" for the active Level 2 tab - the
// same tone-muted fill already used elsewhere (Button's own variants,
// badge treatments), just applied here so the active mode reads as a
// raised tab rather than only an underline + color change. Kept to a
// single shadow step (shadow-sm) and a light tint, not a filled pill -
// this is a navigation control that stays legible next to eight
// siblings, not a card.
function surfaceClasses(tone: "ai" | "atmosphere" | undefined, isActive: boolean) {
  if (!isActive) return "";
  if (tone === "ai") return "bg-ai-muted shadow-sm";
  if (tone === "atmosphere") return "bg-atmosphere-muted shadow-sm";
  return "bg-accent-muted shadow-sm";
}

/**
 * Left/Right (and Home/End) move focus to the adjacent button *within
 * the same row* and activate it immediately - the standard "automatic
 * activation" tabs keyboard pattern (WAI-ARIA Authoring Practices),
 * matching what Tab/Shift+Tab + Enter/Space already give for free on
 * plain `<button>`s. Implemented by walking DOM siblings rather than
 * tracking a parallel refs array - each row already renders nothing
 * but its own same-row buttons, so `previous/nextElementSibling` can't
 * cross into the other row.
 */
function handleRowArrowKey(event: KeyboardEvent<HTMLButtonElement>) {
  const key = event.key;
  if (key !== "ArrowLeft" && key !== "ArrowRight" && key !== "Home" && key !== "End") return;
  event.preventDefault();
  const current = event.currentTarget;
  const row = current.parentElement;
  if (!row) return;
  const buttons = Array.from(row.querySelectorAll<HTMLButtonElement>("button"));
  const index = buttons.indexOf(current);
  if (index === -1) return;
  let nextIndex: number;
  if (key === "Home") nextIndex = 0;
  else if (key === "End") nextIndex = buttons.length - 1;
  else if (key === "ArrowRight") nextIndex = (index + 1) % buttons.length;
  else nextIndex = (index - 1 + buttons.length) % buttons.length;
  const next = buttons[nextIndex];
  next?.focus();
  next?.click();
}

/**
 * A compact, two-level switcher rather than a single flat strip of all
 * nine modes at once: a thin row of the four groups (Watch / Understand
 * / Ask / Study), and directly below it, only the current group's own
 * modes. Quiet and typography-led throughout - active state is always
 * weight/color/a thin underline, never a filled pill or card. Once the
 * active panel has been scrolled (`compact`), both rows collapse into
 * a single thin line so reading a long transcript or chat thread never
 * keeps a two-row nav permanently eating the viewport.
 */
export function WorkspaceNav({ active, onSelect, compact = false, className }: WorkspaceNavProps) {
  const { notice } = useNovaAttention();

  const activeGroup = WORKSPACE_SECTION_GROUPS.find((group) => group.ids.includes(active)) ?? WORKSPACE_SECTION_GROUPS[0]!;
  const [expandedLabel, setExpandedLabel] = useState(activeGroup.label);

  // A deep link from inside a panel (e.g. Overview linking straight to
  // Chapters) changes `active` without ever touching this nav - keep
  // the expanded group in sync with it rather than stranding Level 2
  // on whatever group was last clicked here.
  useEffect(() => {
    setExpandedLabel(activeGroup.label);
  }, [activeGroup.label]);

  const expandedGroup = WORKSPACE_SECTION_GROUPS.find((group) => group.label === expandedLabel) ?? activeGroup;
  const activeSectionDef = WORKSPACE_SECTIONS.find((section) => section.id === active);

  function selectSection(id: WorkspaceSection) {
    const section = WORKSPACE_SECTIONS.find((candidate) => candidate.id === id);
    onSelect(id);
    if (section?.tone === "ai") notice("attention", 900);
  }

  return (
    <nav
      aria-label="Workspace modes"
      className={cn("shrink-0 border-b border-border bg-surface transition-[padding] duration-fast", className)}
    >
      {compact ? (
        <div className="flex items-center gap-3 overflow-x-auto px-3 py-1.5 text-caption sm:px-4">
          {WORKSPACE_SECTION_GROUPS.map((group) => (
            <button
              key={group.label}
              type="button"
              onClick={() => selectSection(group.ids[0]!)}
              onKeyDown={handleRowArrowKey}
              aria-current={group.label === activeGroup.label ? "true" : undefined}
              className={cn(
                "shrink-0 whitespace-nowrap font-semibold uppercase tracking-wider transition-colors duration-fast",
                group.label === activeGroup.label ? "text-text-primary" : "text-text-disabled hover:text-text-secondary",
              )}
            >
              {group.label}
            </button>
          ))}
          {activeSectionDef && (
            <>
              <span className="shrink-0 text-text-disabled" aria-hidden="true">
                ·
              </span>
              <span className={cn("shrink-0 whitespace-nowrap font-medium", toneClasses(activeSectionDef.tone, true))}>
                {activeSectionDef.label}
              </span>
            </>
          )}
        </div>
      ) : (
        <>
          {/* Level 1 — the four groups only. */}
          <div className="flex items-stretch gap-4 overflow-x-auto px-3 pt-2 sm:px-4">
            {WORKSPACE_SECTION_GROUPS.map((group) => {
              const isExpanded = group.label === expandedGroup.label;
              return (
                <button
                  key={group.label}
                  type="button"
                  onClick={() => setExpandedLabel(group.label)}
                  onKeyDown={handleRowArrowKey}
                  aria-expanded={isExpanded}
                  className="group flex shrink-0 flex-col items-center gap-1.5 pb-1.5"
                >
                  <span
                    className={cn(
                      "whitespace-nowrap text-[11px] font-semibold uppercase tracking-wider transition-colors duration-fast",
                      isExpanded ? "text-text-primary" : "text-text-disabled group-hover:text-text-secondary",
                    )}
                  >
                    {group.label}
                  </span>
                  <span
                    className={cn("h-0.5 w-full rounded-full transition-colors duration-fast", isExpanded ? "bg-text-primary" : "bg-transparent")}
                    aria-hidden="true"
                  />
                </button>
              );
            })}
          </div>

          {/* Level 2 — only the expanded group's own modes. */}
          <div className="flex items-stretch gap-1 overflow-x-auto px-3 sm:px-4">
            {expandedGroup.ids.map((id) => {
              const section = WORKSPACE_SECTIONS.find((candidate) => candidate.id === id);
              if (!section) return null;
              const isActive = section.id === active;
              return (
                <button
                  key={section.id}
                  type="button"
                  title={section.label}
                  onClick={() => selectSection(section.id)}
                  onKeyDown={handleRowArrowKey}
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "flex shrink-0 items-center gap-1.5 rounded-t-md border-b-2 px-2.5 py-2 text-body-sm font-medium transition-[background-color,box-shadow,color,border-color] duration-fast",
                    isActive ? "border-current" : "border-transparent hover:bg-surface-hover",
                    toneClasses(section.tone, isActive),
                    surfaceClasses(section.tone, isActive),
                  )}
                >
                  <Icon name={section.icon} size={14} className="shrink-0" />
                  <span className="whitespace-nowrap">{section.label}</span>
                  {section.tone && (
                    <span
                      className={cn("h-1 w-1 shrink-0 rounded-full", underlineClasses(section.tone), !isActive && "opacity-60")}
                      aria-hidden="true"
                    />
                  )}
                </button>
              );
            })}
          </div>
        </>
      )}
    </nav>
  );
}
