"use client";

import { Sidebar } from "@/components/layout/sidebar";

export default function ProjectLayout({ children, params }: { children: React.ReactNode; params: { id: string } }) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar novelId={params.id} />
      <div className="flex-1">{children}</div>
    </div>
  );
}
