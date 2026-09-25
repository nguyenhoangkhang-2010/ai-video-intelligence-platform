"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

/** Catches a render-time error inside the login/register form itself - the cinematic Nova shell in (auth)/layout.tsx keeps rendering above this. */
export default function AuthSegmentError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center gap-3 py-4 text-center">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-error-muted text-error">
        <Icon name="alert" size={18} />
      </div>
      <p className="text-body-sm font-medium text-text-primary">This form hit an unexpected error</p>
      <Button variant="secondary" size="sm" onClick={() => reset()}>
        <Icon name="refresh" size={14} />
        Try again
      </Button>
    </div>
  );
}
