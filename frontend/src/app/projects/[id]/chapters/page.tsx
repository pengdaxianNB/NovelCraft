"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Chapter } from "@/types";
import Link from "next/link";

export default function ChaptersPage() {
  const { id } = useParams<{ id: string }>();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("all");

  useEffect(() => {
    api.listChapters(id).then(setChapters).finally(() => setLoading(false));
  }, [id]);

  const filtered = filter === "all" ? chapters : chapters.filter(c => c.status === filter);

  const handlePublish = async (chapterId: string) => {
    await api.publishChapter(chapterId);
    api.listChapters(id).then(setChapters);
  };

  const statusLabel: Record<string, string> = { draft: "草稿", review: "待审核", published: "已发布" };

  if (loading) return <main className="p-8"><p className="text-muted-foreground">加载中...</p></main>;

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold text-foreground mb-6">章节管理</h1>

      <div className="flex gap-2 mb-4">
        {["all", "draft", "review", "published"].map(s => (
          <Button key={s} variant={filter === s ? "default" : "outline"} size="sm" onClick={() => setFilter(s)}>
            {s === "all" ? "全部" : statusLabel[s] || s}
          </Button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="text-muted-foreground">暂无章节</p>
      ) : (
        <div className="border border-border rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-muted">
              <tr><th className="text-left p-3">序号</th><th className="text-left p-3">标题</th><th className="text-left p-3">字数</th><th className="text-left p-3">状态</th><th className="text-left p-3">更新时间</th><th className="text-left p-3">操作</th></tr>
            </thead>
            <tbody>
              {filtered.map(c => (
                <tr key={c.id} className="border-t border-border">
                  <td className="p-3">第{c.chapter_number}章</td>
                  <td className="p-3 font-medium">{c.title}</td>
                  <td className="p-3 text-muted-foreground">{c.word_count.toLocaleString()}</td>
                  <td className="p-3"><Badge variant={c.status}>{statusLabel[c.status] || c.status}</Badge></td>
                  <td className="p-3 text-muted-foreground">{new Date(c.updated_at).toLocaleDateString("zh-CN")}</td>
                  <td className="p-3 flex gap-2">
                    <Link href={`/projects/${id}/review`}><Button size="sm" variant="outline">审阅</Button></Link>
                    {c.status === "review" && <Button size="sm" onClick={() => handlePublish(c.id)}>发布</Button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
