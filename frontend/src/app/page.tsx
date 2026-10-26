"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { Landing } from "@/components/landing/Landing";
import { Spinner } from "@/components/ui/Spinner";
import { useAuth } from "@/hooks/useAuth";
import { ROUTES } from "@/lib/constants";

/**
 * An authenticated visitor still lands on their library, not a
 * marketing page they've already moved past - but an unauthenticated
 * one now sees a real landing page instead of being redirected
 * straight to /login with no arrival experience at all.
 */
export default function RootPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading || !isAuthenticated) return;
    router.replace(ROUTES.library);
  }, [isLoading, isAuthenticated, router]);

  if (isLoading || isAuthenticated) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-bg">
        <Spinner size={24} />
      </div>
    );
  }

  return <Landing />;
}
