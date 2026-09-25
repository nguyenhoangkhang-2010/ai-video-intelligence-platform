"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Icon } from "@/components/ui/Icon";
import { Mark } from "@/components/ui/Logo";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

/**
 * Replaces the old sidebar. A sidebar earns its width by holding many
 * destinations; this product has exactly two (Library, Account), and
 * every real destination already carries its own header (Library's
 * PageHeader, the workspace's own WorkspaceHeader) - a persistent
 * vertical rail was pure chrome. A slim top strip gives the same
 * always-available navigation back for zero width cost, which matters
 * here specifically because the workspace wants the full viewport for
 * a video-first composition, not a permanent side column.
 */
export function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { state: novaState } = useNovaAttention();
  const isLibraryActive = pathname === ROUTES.library || pathname.startsWith("/videos/");
  const isAccountActive = pathname === ROUTES.account;
  const novaActive = novaState !== "idle";

  return (
    <header className="flex h-12 shrink-0 items-center justify-between border-b border-border bg-surface px-4 sm:px-5">
      <Link href={ROUTES.library} className="flex items-center gap-2 text-text-primary">
        <span className="relative">
          <Mark size={21} className="text-accent" />
          <span
            className={cn(
              "absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-ai ring-2 ring-surface transition-opacity duration-base",
              novaActive ? "opacity-100 animate-pulse" : "opacity-0",
            )}
            aria-hidden="true"
          />
        </span>
        <span className="hidden font-display text-body-sm font-semibold tracking-tight sm:inline">
          Reel<span className="text-ai">Sense</span>
        </span>
      </Link>

      <nav aria-label="Primary" className="flex items-center gap-1">
        <Link
          href={ROUTES.library}
          aria-current={isLibraryActive ? "page" : undefined}
          className={cn(
            "rounded px-3 py-1.5 text-body-sm font-medium transition-colors duration-fast",
            isLibraryActive
              ? "text-text-primary"
              : "text-text-secondary hover:bg-surface-hover hover:text-text-primary",
          )}
        >
          Library
        </Link>

        <span className="mx-1 h-4 w-px bg-border" aria-hidden="true" />

        <Link
          href={ROUTES.account}
          aria-current={isAccountActive ? "page" : undefined}
          title={user?.username ?? "Account"}
          className={cn(
            "flex items-center gap-2 rounded px-2 py-1 transition-colors duration-fast",
            isAccountActive ? "text-text-primary" : "hover:bg-surface-hover",
          )}
        >
          <span className="flex h-6 w-6 items-center justify-center rounded-full bg-surface-elevated text-text-secondary">
            <Icon name="user" size={13} />
          </span>
          <span className="hidden max-w-[9rem] truncate text-body-sm font-medium text-text-primary md:inline">
            {user?.username ?? "Account"}
          </span>
        </Link>

        <button
          type="button"
          onClick={logout}
          title="Log out"
          aria-label="Log out"
          className="flex h-8 w-8 items-center justify-center rounded text-text-muted transition-colors duration-fast hover:bg-surface-hover hover:text-error"
        >
          <Icon name="logout" size={15} />
        </button>
      </nav>
    </header>
  );
}
