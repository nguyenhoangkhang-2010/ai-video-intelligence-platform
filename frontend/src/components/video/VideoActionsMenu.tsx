"use client";

import { useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";
import type { Video } from "@/types/video";

/** The per-video "…" menu (currently: Delete), shared by the dial and list views. */
export function VideoActionsMenu({
  video,
  onDelete,
  className,
}: {
  video: Video;
  onDelete: (video: Video) => void;
  className?: string;
}) {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className={cn("relative shrink-0", className)}>
      <button
        type="button"
        aria-label="Video actions"
        aria-haspopup="menu"
        aria-expanded={menuOpen}
        onClick={() => setMenuOpen((value) => !value)}
        className={cn(
          "flex h-8 w-8 items-center justify-center border border-transparent text-text-secondary transition-colors duration-fast hover:border-text-primary/50 hover:bg-surface-elevated hover:text-text-primary",
          menuOpen && "border-text-primary/50 bg-surface-elevated text-text-primary",
        )}
      >
        <Icon name="more" size={16} />
      </button>
      {menuOpen && (
        <>
          <div className="fixed inset-0 z-dropdown" onClick={() => setMenuOpen(false)} />
          <div
            role="menu"
            aria-label="Video actions"
            className="absolute right-0 top-9 z-dropdown w-40 border border-text-primary/70 bg-surface-elevated py-1 shadow-step-ink"
          >
            <button
              type="button"
              role="menuitem"
              onClick={() => {
                setMenuOpen(false);
                onDelete(video);
              }}
              className="flex w-full items-center gap-2 px-3 py-2 text-left text-body-sm text-error hover:bg-error-muted"
            >
              <Icon name="trash" size={14} />
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}
