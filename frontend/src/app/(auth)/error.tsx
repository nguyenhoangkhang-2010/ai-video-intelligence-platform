"use client";

import { useEffect } from "react";

import { DialRing } from "@/components/dial/DialRing";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";

/** Catches a render-time error inside the login/register form itself - the dial shell in (auth)/layout.tsx keeps rendering above this. */
export default function AuthSegmentError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    // eslint-disable-next-line no-console
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center gap-3 py-4 text-center">
      <DialRing size={48} ticks={12} majorEvery={3} caseWidth={7} progress={1} tone="error">
        <Icon name="alert" size={16} className="text-error" />
      </DialRing>
      <p className="text-body-sm font-medium text-text-primary">This form hit an unexpected error</p>
      <Button variant="secondary" size="sm" onClick={() => reset()}>
        <Icon name="refresh" size={14} />
        Try again
      </Button>
    </div>
  );
}
