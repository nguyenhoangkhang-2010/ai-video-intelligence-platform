import Link from "next/link";

import { DialRing } from "@/components/dial/DialRing";
import { Button } from "@/components/ui/Button";
import { Icon } from "@/components/ui/Icon";
import { ROUTES } from "@/lib/constants";

export default function NotFound() {
  return (
    <div className="flex h-screen w-full flex-col items-center justify-center gap-3 bg-bg text-center">
      <DialRing size={72} ticks={12} majorEvery={3} caseWidth={7}>
        <Icon name="file-warning" size={22} className="text-text-secondary" />
      </DialRing>
      <div>
        <p className="font-display text-heading font-semibold text-text-primary">Page not found</p>
        <p className="mt-1 text-body-sm text-text-secondary">
          That page doesn&apos;t exist or may have moved.
        </p>
      </div>
      <Link href={ROUTES.library}>
        <Button variant="secondary" size="sm" className="mt-1">
          Back to library
        </Button>
      </Link>
    </div>
  );
}
