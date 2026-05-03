"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { Novel, Chapter, Outline } from "@/types";

export default function WorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const [novel, setNovel] = useState<Novel | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getNovel(id),
      api.listChapters(id),
      api.listOutlines(id),
    ]).then(([n, c, o]) => {
      setNovel(n);
      setChapters(c);
      setOutlines(o);
      setLoading(false);
    });
  }, [id]);

  const handleGenerateChapter = async () => {
    const result = await api.generateChapter(id, {});
    alert(`生成任务已创建: ${result.task_id}`);
  };

  if (loading) return <main className="p-8"><p className="text-muted-foreground">加载中...</p></main>;
  if (!novel) return <main className="p-8"><p className="text-muted-foreground">小说未找到</p></main>;

  const latestChapter = chapters[chapters.length - 1];

  return (
    <div className="flex h-full">
      <aside className="w-64 border-r border-border p-4 overflow-y-auto">
        <h3 className="font-semibold mb-3">大纲结构</h3>
        {outlines.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无大纲，前往设定工坊创建</p>
        ) : (
          <OutlineTree outlines={outlines} />
        )}
      </aside>
      <main className="flex-1 p-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold text-foreground">{novel.title}</h1>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant={novel.genre}>{novel.genre}</Badge>
              <Badge variant={novel.status}>{novel.status === "writing" ? "连载中" : novel.status}</Badge>
            </div>
          </div>
          <Button onClick={handleGenerateChapter} size="lg">生成下一章</Button>
        </div>

        {novel.synopsis && <p className="text-muted-foreground mb-6">{novel.synopsis}</p>}

        <div className="grid grid-cols-3 gap-4 mb-8">
          <Card><CardHeader><h4 className="text-sm text-muted-foreground">总章节</h4></CardHeader><CardContent><p className="text-2xl font-bold">{novel.chapter_count}</p></CardContent></Card>
          <Card><CardHeader><h4 className="text-sm text-muted-foreground">已发布</h4></CardHeader><CardContent><p className="text-2xl font-bold text-green-600">{novel.published_count}</p></CardContent></Card>
          <Card><CardHeader><h4 className="text-sm text-muted-foreground">待审核</h4></CardHeader><CardContent><p className="text-2xl font-bold text-yellow-600">{chapters.filter(c => c.status === "review").length}</p></CardContent></Card>
        </div>

        <h2 className="text-xl font-semibold mb-4">最近章节</h2>
        {latestChapter && (
          <Card>
            <CardHeader><h3 className="font-semibold">第{latestChapter.chapter_number}章 {latestChapter.title}</h3></CardHeader>
            <CardContent>
              <Badge variant={latestChapter.status} className="mb-2">{latestChapter.status}</Badge>
              <p className="text-sm text-muted-foreground">{latestChapter.word_count} 字</p>
              {latestChapter.content && <p className="mt-2 text-sm line-clamp-4">{latestChapter.content}</p>}
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
}

function OutlineTree({ outlines, depth = 0 }: { outlines: Outline[]; depth?: number }) {
  return (
    <ul className={`space-y-1 ${depth > 0 ? "ml-4" : ""}`}>
      {outlines.map((o) => (
        <li key={o.id}>
          <div className="flex items-center gap-1 py-0.5">
            <Badge variant={o.status} className="text-[10px]">{o.level}</Badge>
            <span className="text-sm truncate">{o.title}</span>
          </div>
          {o.children && o.children.length > 0 && <OutlineTree outlines={o.children} depth={depth + 1} />}
        </li>
      ))}
    </ul>
  );
}
