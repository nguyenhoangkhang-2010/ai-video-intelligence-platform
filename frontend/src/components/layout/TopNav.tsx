"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { useNovaAttention } from "@/components/3d/NovaAttentionContext";
import { Icon } from "@/components/ui/Icon";
import { Mark } from "@/components/ui/Logo";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/lib/constants";
import { cn } from "@/lib/utils";

/** Live HH:MM:SS - the case's own running seconds, client-only so SSR markup never mismatches. */
function CaseClock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const id = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(id);
  }, []);
  if (!now) return <span className="w-[4.6rem]" aria-hidden="true" />;
  const pad = (n: number) => String(n).padStart(2, "0");
  return (
    <time className="font-mono text-caption tabular-nums text-text-secondary" dateTime={now.toISOString()} aria-hidden="true">
      {pad(now.getHours())}:{pad(now.getMinutes())}:{pad(now.getSeconds())}
    </time>
  );
}

/**
 * The case band: a slim titanium strip carrying the wordmark, the two
 * real destinations (Library, Account) as engraved index labels, a
 * running case clock, and the Nova activity pip. Two destinations
 * don't earn a sidebar; the workspace wants every pixel of width for
 * its dial.
 */
export function TopNav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { state: novaState } = useNovaAttention();
  const isLibraryActive = pathname === ROUTES.library || pathname.startsWith("/videos/") || pathname.startsWith("/library");
  const isAccountActive = pathname === ROUTES.account;
  const novaActive = novaState !== "idle";

  const linkClass = (active: boolean) =>
    cn(
      "index-label relative flex h-12 items-center px-3 transition-colors duration-fast",
      active ? "text-text-primary" : "text-text-secondary hover:text-text-primary",
    );

  return (
    <header className="flex h-12 shrink-0 items-stretch justify-between border-b-2 border-text-primary bg-bg px-4 sm:px-6">
      <Link href={ROUTES.library} className="flex items-center gap-2.5 text-text-primary">
        <span className="relative">
          <Mark size={22} />
          <span
            className={cn(
              "absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full border-2 border-bg bg-ai transition-opacity duration-base",
              novaActive ? "opacity-100" : "opacity-0",
            )}
            aria-hidden="true"
          />
        </span>
        <span className="hidden font-display text-[0.9rem] font-semibold uppercase tracking-[0.22em] sm:inline">
          Reel<span className="text-accent">sense</span>
        </span>
      </Link>

      <nav aria-label="Primary" className="flex items-stretch">
        <Link href={ROUTES.library} aria-current={isLibraryActive ? "page" : undefined} className={linkClass(isLibraryActive)}>
          Library
          {isLibraryActive && <span className="absolute inset-x-3 -bottom-[2px] h-[3px] bg-lume" aria-hidden="true" />}
        </Link>

        <Link
          href={ROUTES.account}
          aria-current={isAccountActive ? "page" : undefined}
          title={user?.username ?? "Account"}
          className={cn(linkClass(isAccountActive), "gap-2")}
        >
          <Icon name="user" size={13} />
          <span className="hidden max-w-[9rem] truncate md:inline">{user?.username ?? "Account"}</span>
          {isAccountActive && <span className="absolute inset-x-3 -bottom-[2px] h-[3px] bg-lume" aria-hidden="true" />}
        </Link>

        <span className="mx-2 my-3 w-px bg-text-primary/25" aria-hidden="true" />

        <div className="hidden items-center pr-2 sm:flex">
          <CaseClock />
        </div>

        <button
          type="button"
          onClick={logout}
          title="Log out"
          aria-label="Log out"
          className="flex w-10 items-center justify-center text-text-secondary transition-colors duration-fast hover:text-error"
        >
          <Icon name="logout" size={15} />
        </button>
      </nav>
    </header>
  );
}
