"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Novel } from "@/types";

export default function Dashboard() {
  const [novels, setNovels] = useState<Novel[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listNovels().then(setNovels).finally(() => setLoading(false));
  }, []);

  const activeNovel = novels.find((n) => n.status === "writing");

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8">
        <h1 className="text-3xl font-bold text-foreground mb-6">仪表盘</h1>

        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card><CardHeader><h3 className="text-sm text-muted-foreground">全部小说</h3></CardHeader><CardContent><p className="text-2xl font-bold">{novels.length}</p></CardContent></Card>
          <Card><CardHeader><h3 className="text-sm text-muted-foreground">连载中</h3></CardHeader><CardContent><p className="text-2xl font-bold">{novels.filter((n) => n.status === "writing").length}</p></CardContent></Card>
          <Card><CardHeader><h3 className="text-sm text-muted-foreground">已完成</h3></CardHeader><CardContent><p className="text-2xl font-bold">{novels.filter((n) => n.status === "completed").length}</p></CardContent></Card>
        </div>

        {loading ? <p className="text-muted-foreground">加载中...</p> : novels.length === 0 ? (
          <div className="text-center py-12"><p className="text-muted-foreground mb-4">暂无小说</p><Link href="/projects"><Button>创建第一部小说</Button></Link></div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {novels.slice(0, 6).map((novel) => (
              <Link key={novel.id} href={`/projects/${novel.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer">
                  <CardHeader><div className="flex items-center justify-between"><h3 className="font-semibold">{novel.title}</h3><Badge variant={novel.genre}>{novel.genre}</Badge></div></CardHeader>
                  <CardContent><p className="text-sm text-muted-foreground line-clamp-2">{novel.synopsis || "暂无简介"}</p><p className="text-xs text-muted-foreground mt-2">进度：{novel.published_count}/{novel.chapter_count} 章</p></CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
