import { cn } from "@/lib/utils";

const variants: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  review: "bg-yellow-100 text-yellow-700",
  published: "bg-green-100 text-green-700",
  planning: "bg-blue-100 text-blue-700",
  writing: "bg-purple-100 text-purple-700",
  completed: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
  queued: "bg-gray-100 text-gray-500",
  running: "bg-blue-100 text-blue-700",
  default: "bg-gray-100 text-gray-700",
};

export function Badge({ variant = "default", className, children }: { variant?: string; className?: string; children: React.ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", variants[variant] || variants.default, className)}>
      {children}
    </span>
  );
}
