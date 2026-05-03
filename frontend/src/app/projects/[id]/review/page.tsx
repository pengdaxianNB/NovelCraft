"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Chapter } from "@/types";

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [selected, setSelected] = useState<Chapter | null>(null);
  const [editContent, setEditContent] = useState("");
  const [loading, setLoading] = useState(true);

  const fetchChapters = () => api.listChapters(id).then(setChapters);
  useEffect(() => { fetchChapters().finally(() => setLoading(false)); }, [id]);

  const reviewChapters = chapters.filter(c => c.status === "draft" || c.status === "review");

  const openChapter = async (c: Chapter) => {
    const full = await api.getChapter(c.id);
    setSelected(full);
    setEditContent(full.content || "");
  };

  const handleSave = async () => {
    if (!selected) return;
    await api.updateChapter(selected.id, { content: editContent });
    setSelected(null);
    fetchChapters();
  };

  const handleApprove = async () => {
    if (!selected) return;
    if (editContent !== selected.content) await api.updateChapter(selected.id, { content: editContent });
    await api.publishChapter(selected.id);
    setSelected(null);
    fetchChapters();
  };

  const handleRewrite = async () => {
    if (!selected) return;
    await api.rewriteChapter(selected.id);
    alert("已触发重写任务");
  };

  if (loading) return <main className="p-8"><p className="text-muted-foreground">加载中...</p></main>;

  return (
    <div className="flex h-full">
      <aside className="w-72 border-r border-border p-4 overflow-y-auto">
        <h3 className="font-semibold mb-3">待审核队列</h3>
        {reviewChapters.length === 0 ? (
          <p className="text-sm text-muted-foreground">没有待审核的章节</p>
        ) : (
          <div className="space-y-2">
            {reviewChapters.map(c => (
              <Card key={c.id} className={`cursor-pointer hover:shadow-md transition-shadow ${selected?.id === c.id ? "ring-2 ring-primary" : ""}`} onClick={() => openChapter(c)}>
                <CardContent className="p-3">
                  <div className="flex items-center justify-between"><span className="font-medium text-sm">第{c.chapter_number}章</span><Badge variant={c.status}>{c.status}</Badge></div>
                  <p className="text-xs text-muted-foreground mt-1">{c.word_count} 字</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </aside>

      <main className="flex-1 p-8">
        {!selected ? (
          <div className="flex items-center justify-center h-full"><p className="text-muted-foreground">选择左侧章节开始审核</p></div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">第{selected.chapter_number}章 {selected.title}</h2>
              <div className="flex gap-2">
                <Button variant="outline" onClick={handleRewrite}>触发重写</Button>
                <Button variant="outline" onClick={handleSave}>保存修改</Button>
                <Button onClick={handleApprove}>批准发布</Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <Card><CardHeader><h4 className="font-medium">生成内容</h4></CardHeader><CardContent><div className="prose prose-sm max-w-none whitespace-pre-wrap text-sm">{selected.content || "暂无内容"}</div></CardContent></Card>
              <Card><CardHeader><h4 className="font-medium">编辑区</h4></CardHeader><CardContent><textarea className="w-full h-96 p-3 border border-border rounded-md bg-background text-sm font-mono" value={editContent} onChange={e => setEditContent(e.target.value)} /></CardContent></Card>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
