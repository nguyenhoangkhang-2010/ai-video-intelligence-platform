"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

/**
 * Catches a render-time error anywhere under the authenticated shell
 * (Library, Upload Studio, Account, the video workspace) - TopNav and
 * RequireAuth in (app)/layout.tsx keep rendering above this, since
 * error.tsx only replaces the segment that actually crashed. Without
 * this file, App Router had no boundary here at all: a thrown error
 * fell through to Next's own default handling instead of a real,
 * on-brand recovery screen with a working retry.
 */
export default function AppSegmentError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-3 bg-bg p-6 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-error-muted text-error">
        <Icon name="alert" size={22} />
      </div>
      <div className="max-w-sm">
        <p className="font-display text-heading font-semibold text-text-primary">Something went wrong</p>
        <p className="mt-1 text-body-sm text-text-muted">
          This screen hit an unexpected error. Your data is safe — try again, or head back to the library.
        </p>
      </div>
      <div className="mt-1 flex items-center gap-2">
        <Button variant="secondary" size="sm" onClick={() => reset()}>
          <Icon name="refresh" size={14} />
          Try again
        </Button>
      </div>
    </div>
  );
}
