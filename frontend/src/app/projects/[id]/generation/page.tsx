"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import type { GenerationTask } from "@/types";

export default function GenerationPage() {
  const { id } = useParams<{ id: string }>();
  const [tasks, setTasks] = useState<GenerationTask[]>([]);
  const [streamText, setStreamText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [outlineForm, setOutlineForm] = useState({ level: "chapter", parent_id: "", count: 5 });
  const [chapterForm, setChapterForm] = useState({ words_per_chapter: 3000 });
  const eventSourceRef = useRef<EventSource | null>(null);

  const fetchTasks = () => api.listTasks().then(setTasks);

  useEffect(() => { fetchTasks(); }, [id]);

  useEffect(() => {
    return () => { if (eventSourceRef.current) eventSourceRef.current.close(); };
  }, []);

  const handleGenerateOutline = async () => {
    const result = await api.generateOutline(id, outlineForm);
    await fetchTasks();
    alert(`大纲生成任务已创建: ${result.task_id}`);
  };

  const handleGenerateChapter = async () => {
    const result = await api.generateChapter(id, { words_per_chapter: chapterForm.words_per_chapter });
    setActiveTaskId(result.task_id);
    setStreamText("");
    setStreaming(true);

    if (eventSourceRef.current) eventSourceRef.current.close();
    const es = new EventSource(api.getStreamUrl(result.task_id));
    eventSourceRef.current = es;

    es.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.text) setStreamText(prev => prev + data.text);
        if (data.stage === "complete") {
          setStreaming(false);
          es.close();
          fetchTasks();
        }
      } catch { /* ignore parse errors */ }
    });

    es.onerror = () => { setStreaming(false); es.close(); };
    await fetchTasks();
  };

  const taskStatusLabel: Record<string, string> = { queued: "排队中", running: "执行中", done: "已完成", failed: "失败", cancelled: "已取消" };

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold text-foreground mb-6">生成控制台</h1>

      <div className="grid grid-cols-2 gap-6 mb-8">
        <Card>
          <CardHeader><h3 className="font-semibold">大纲生成</h3></CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-sm mb-1">层级</label>
                <select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={outlineForm.level} onChange={e => setOutlineForm({ ...outlineForm, level: e.target.value })}>
                  <option value="volume">卷</option><option value="arc">弧</option><option value="chapter">章</option>
                </select>
              </div>
              <div>
                <label className="block text-sm mb-1">数量</label>
                <input type="number" className="w-full px-3 py-2 border border-border rounded-md bg-background" value={outlineForm.count} onChange={e => setOutlineForm({ ...outlineForm, count: Number(e.target.value) })} min={1} max={20} />
              </div>
              <Button onClick={handleGenerateOutline}>生成大纲</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><h3 className="font-semibold">章节生成</h3></CardHeader>
          <CardContent>
            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-sm mb-1">本章目标字数</label>
                <input type="number" className="w-full px-3 py-2 border border-border rounded-md bg-background" value={chapterForm.words_per_chapter} onChange={e => setChapterForm({ words_per_chapter: Number(e.target.value) })} />
              </div>
              <Button onClick={handleGenerateChapter} disabled={streaming}>{streaming ? "生成中..." : "生成下一章"}</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {streamText && (
        <Card className="mb-8">
          <CardHeader><h3 className="font-semibold">实时生成预览 {streaming && <span className="text-sm text-blue-500 animate-pulse ml-2">生成中...</span>}</h3></CardHeader>
          <CardContent><div className="whitespace-pre-wrap text-sm font-mono bg-muted p-4 rounded-md max-h-96 overflow-y-auto">{streamText || "等待内容..."}</div></CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><div className="flex items-center justify-between"><h3 className="font-semibold">任务历史</h3><Button size="sm" variant="outline" onClick={fetchTasks}>刷新</Button></div></CardHeader>
        <CardContent>
          {tasks.length === 0 ? <p className="text-muted-foreground text-sm">暂无任务</p> : (
            <div className="space-y-2">
              {tasks.slice(0, 20).map(t => (
                <div key={t.id} className="flex items-center justify-between py-2 border-b border-border last:border-0">
                  <div>
                    <span className="text-sm font-medium">{t.task_type === "chapter" ? "章节生成" : "大纲生成"}</span>
                    <span className="text-xs text-muted-foreground ml-2">{new Date(t.created_at).toLocaleString("zh-CN")}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={t.status}>{taskStatusLabel[t.status] || t.status}</Badge>
                    {t.status === "running" && <Button size="sm" variant="outline" onClick={() => { api.cancelTask(t.id); fetchTasks(); }}>取消</Button>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </main>
  );
}
