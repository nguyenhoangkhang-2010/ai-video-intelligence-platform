"use client";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/hooks/useAuth";

/**
 * GET /users/me returns exactly {id, username, email} (see
 * docs/api/rest_api.md, Authentication section) — no profile-update,
 * preferences, or appearance-settings endpoint exists, so this stays
 * a read-only identity summary plus logout. No "Preferences" or
 * "Appearance" section is invented here — a toggle that doesn't
 * persist anywhere real would be worse than not having one.
 */
export default function AccountPage() {
  const { user, logout } = useAuth();
  const initial = user?.username?.trim().charAt(0).toUpperCase() || "?";

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <div
        className="pointer-events-none absolute -top-24 left-1/2 z-0 h-[420px] w-[420px] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgb(var(--color-accent)/0.08),transparent_70%)]"
        aria-hidden="true"
      />

      <div className="relative z-10 flex h-full flex-col overflow-hidden">
        <PageHeader eyebrow="Account" title="Your profile" />

        <div className="flex-1 overflow-y-auto px-6 py-10 sm:px-8">
          <div className="mx-auto flex max-w-md flex-col items-center gap-3 text-center">
            <span className="flex h-20 w-20 items-center justify-center rounded-full bg-accent-muted font-display text-display font-semibold text-accent">
              {initial}
            </span>
            <div>
              <p className="text-heading font-display font-semibold text-text-primary">{user?.username}</p>
              <p className="mt-0.5 text-body-sm text-text-muted">{user?.email}</p>
            </div>
            <span className="mt-1 rounded-full border border-border-strong px-2.5 py-0.5 font-mono text-caption text-text-muted">
              #{user?.id}
            </span>
          </div>

          <div className="mx-auto mt-10 max-w-md">
            <p className="mb-2 text-label font-semibold uppercase tracking-wide text-text-secondary">Session</p>
            <div className="flex items-center justify-between rounded-lg border border-border bg-surface px-5 py-4">
              <div>
                <p className="text-body-sm font-medium text-text-primary">Sign out</p>
                <p className="text-caption text-text-muted">End your session on this device.</p>
              </div>
              <Button variant="secondary" size="sm" onClick={logout}>
                <Icon name="logout" size={14} />
                Log out
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
