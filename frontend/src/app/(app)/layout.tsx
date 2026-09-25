import { RequireAuth } from "@/components/layout/RequireAuth";
import { TopNav } from "@/components/layout/TopNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <RequireAuth>
      <div className="flex h-screen w-full flex-col overflow-hidden bg-bg">
        <TopNav />
        <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">{children}</main>
      </div>
    </RequireAuth>
  );
}
