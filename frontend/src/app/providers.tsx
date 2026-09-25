"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { NovaAmbient } from "@/components/3d/NovaAmbient";
import { NovaAttentionProvider } from "@/components/3d/NovaAttentionContext";
import { AuthProvider } from "@/hooks/useAuth";

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 30_000,
          },
        },
      }),
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <NovaAttentionProvider>
          {children}
          <NovaAmbient />
        </NovaAttentionProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
