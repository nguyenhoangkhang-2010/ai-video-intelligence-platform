import { Spinner } from "@/components/ui/Spinner";

export default function GlobalLoading() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-bg">
      <Spinner size={24} />
    </div>
  );
}
