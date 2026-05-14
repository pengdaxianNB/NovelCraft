"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import type { Novel } from "@/types";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function ProjectsPage() {
  const [novels, setNovels] = useState<Novel[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ title: "", genre: "玄幻", synopsis: "" });
  const router = useRouter();

  const fetchNovels = () => api.listNovels().then(setNovels).catch((e: any) => setError(e.message || "加载小说列表失败")).finally(() => setLoading(false));
  useEffect(() => { fetchNovels(); }, []);

  const handleCreate = async () => {
    const novel = await api.createNovel({
      title: form.title,
      genre: form.genre,
      synopsis: form.synopsis || null,
      style_config: { tone: "热血", pov: "第三人称", words_per_chapter: 3000, custom_instructions: "" },
      schedule_config: { enabled: false, cron: "0 */6 * * *" },
    });
    setShowCreate(false);
    setForm({ title: "", genre: "玄幻", synopsis: "" });
    router.push(`/projects/${novel.id}`);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-3xl font-bold text-foreground">小说列表</h1>
          <Button onClick={() => setShowCreate(true)}>+ 创建新小说</Button>
        </div>

        <Dialog open={showCreate} onClose={() => setShowCreate(false)} title="创建新小说">
          <div className="flex flex-col gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">书名</label>
              <input className="w-full px-3 py-2 border border-border rounded-md bg-background" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="输入书名..." />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">题材</label>
              <select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={form.genre} onChange={(e) => setForm({ ...form, genre: e.target.value })}>
                {["玄幻", "都市", "言情", "仙侠", "科幻", "悬疑", "历史", "游戏"].map((g) => (
                  <option key={g} value={g}>{g}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">简介</label>
              <textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={3} value={form.synopsis} onChange={(e) => setForm({ ...form, synopsis: e.target.value })} placeholder="一句话介绍你的小说..." />
            </div>
            <Button onClick={handleCreate} disabled={!form.title}>创建</Button>
          </div>
        </Dialog>

        {error ? (
          <p className="text-red-600">出错了：{error}</p>
        ) : loading ? (
          <p className="text-muted-foreground">加载中...</p>
        ) : novels.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">还没有小说，创建你的第一部吧</p>
            <Button onClick={() => setShowCreate(true)}>+ 创建新小说</Button>
          </div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {novels.map((novel) => (
              <Link key={novel.id} href={`/projects/${novel.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <h3 className="font-semibold">{novel.title}</h3>
                      <Badge variant={novel.status}>{novel.status === "writing" ? "连载中" : novel.status}</Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Badge variant={novel.genre} className="mb-2">{novel.genre}</Badge>
                    <p className="text-sm text-muted-foreground line-clamp-2">{novel.synopsis || "暂无简介"}</p>
                    <p className="text-xs text-muted-foreground mt-3">已发布 {novel.published_count} / {novel.chapter_count} 章</p>
                    <div className="mt-2 w-full bg-muted rounded-full h-1.5">
                      <div className="bg-primary h-1.5 rounded-full" style={{ width: `${novel.chapter_count > 0 ? (novel.published_count / Math.max(novel.chapter_count, 1)) * 100 : 0}%` }} />
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
