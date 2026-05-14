"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface SidebarProps {
  novelId?: string;
}

export function Sidebar({ novelId }: SidebarProps) {
  const pathname = usePathname();

  const links = [
    { href: "/", label: "仪表盘", icon: "📊" },
    { href: "/projects", label: "小说列表", icon: "📚" },
  ];

  const novelLinks = novelId
    ? [
        { href: `/projects/${novelId}`, label: "工作台", icon: "✍️" },
        { href: `/projects/${novelId}/settings`, label: "设定工坊", icon: "⚙️" },
        { href: `/projects/${novelId}/outlines`, label: "大纲管理", icon: "📋" },
        { href: `/projects/${novelId}/chapters`, label: "章节管理", icon: "📖" },
        { href: `/projects/${novelId}/review`, label: "审核编辑", icon: "🔍" },
        { href: `/projects/${novelId}/generation`, label: "生成控制", icon: "🤖" },
      ]
    : [];

  return (
    <aside className="w-56 min-h-screen border-r border-border bg-background p-4 flex flex-col gap-1">
      <h2 className="text-lg font-bold mb-4 px-2">Novel Agent</h2>
      {[...links, ...novelLinks].map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-md text-sm transition-colors",
            pathname === link.href ? "bg-muted font-medium" : "hover:bg-muted/50 text-muted-foreground",
          )}
        >
          <span>{link.icon}</span> {link.label}
        </Link>
      ))}
    </aside>
  );
}
