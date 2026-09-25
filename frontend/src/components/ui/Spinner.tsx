import { Icon } from "@/components/ui/Icon";
import { cn } from "@/lib/utils";

export function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <Icon
      name="spinner"
      size={size}
      className={cn("animate-spin text-text-muted", className)}
    />
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div className={cn("skeleton rounded", className)} />;
}
