"use client";

import { DialRing, type DialTone } from "@/components/dial/DialRing";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { PageHeader } from "@/components/ui/PageHeader";
import { useAuth } from "@/hooks/useAuth";
import { useVideos } from "@/hooks/useVideos";

function formatReserve(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours > 0 ? `${hours}h ${String(minutes).padStart(2, "0")}m` : `${minutes}m`;
}

/**
 * The case back: identity engraved in the centre, and the library's
 * real numbers as complications around it. GET /users/me returns
 * exactly {id, username, email} (see docs/api/rest_api.md) and no
 * profile/preferences endpoint exists, so nothing here is editable -
 * the complications are computed from the user's own real video list,
 * never invented study scores.
 */
export default function AccountPage() {
  const { user, logout } = useAuth();
  const videos = useVideos();
  const initial = user?.username?.trim().charAt(0).toUpperCase() || "?";

  const list = videos.data ?? [];
  const total = list.length;
  const processed = list.filter((video) => video.status === "processed").length;
  const inProgress = list.filter((video) => video.status === "processing" || video.status === "uploaded").length;
  const seconds = list.reduce((sum, video) => sum + (video.duration || 0), 0);

  const complications: Array<{ label: string; value: string; progress: number | null; tone: DialTone }> = [
    { label: "Videos", value: String(total), progress: null, tone: "lume" },
    { label: "Ready", value: `${processed}/${total}`, progress: total ? processed / total : 0, tone: "lume" },
    { label: "In the works", value: String(inProgress), progress: total ? inProgress / total : 0, tone: "ai" },
    { label: "Reserve", value: formatReserve(seconds), progress: null, tone: "atmosphere" },
  ];

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <PageHeader eyebrow="Account · case back" title="Your profile" />

      <div className="flex-1 overflow-y-auto px-6 py-10 sm:px-10">
        <div className="mx-auto grid max-w-5xl grid-cols-1 items-center gap-12 lg:grid-cols-[minmax(0,420px)_1fr]">
          <div className="mx-auto aspect-square w-full max-w-[420px]">
            <DialRing ticks={60} caseWidth={4} emphasized>
              <div className="flex flex-col items-center text-center">
                <span className="flex h-20 w-20 items-center justify-center rounded-full border-[3px] border-text-primary bg-lume font-display text-display font-semibold text-lume-on">
                  {initial}
                </span>
                <p className="mt-4 font-display text-heading font-semibold text-text-primary">{user?.username}</p>
                <p className="mt-0.5 text-body-sm text-text-secondary">{user?.email}</p>
                <span className="index-label mt-3 border border-text-primary/50 px-2 py-0.5 text-text-secondary">
                  Serial No. {String(user?.id ?? 0).padStart(5, "0")}
                </span>
              </div>
            </DialRing>
          </div>

          <div className="flex flex-col gap-10">
            <section>
              <p className="index-label mb-5 text-text-secondary">Complications</p>
              <div className="grid grid-cols-2 gap-6 sm:grid-cols-4">
                {complications.map((item) => (
                  <div key={item.label} className="flex flex-col items-center text-center">
                    <div className="aspect-square w-full max-w-[120px]">
                      <DialRing ticks={12} majorEvery={3} caseWidth={7} progress={item.progress} tone={item.tone}>
                        <span className="font-mono text-body font-medium text-text-primary">
                          {videos.isLoading ? "…" : item.value}
                        </span>
                      </DialRing>
                    </div>
                    <span className="index-label mt-3 text-text-secondary">{item.label}</span>
                  </div>
                ))}
              </div>
            </section>

            <section className="border-t-2 border-text-primary pt-6">
              <p className="index-label mb-3 text-text-secondary">Session</p>
              <div className="flex items-center justify-between gap-4 border border-text-primary/50 bg-surface-elevated px-5 py-4">
                <div>
                  <p className="text-body-sm font-semibold text-text-primary">Sign out</p>
                  <p className="text-caption text-text-secondary">End your session on this device.</p>
                </div>
                <Button variant="secondary" size="sm" onClick={logout}>
                  <Icon name="logout" size={14} />
                  Log out
                </Button>
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
