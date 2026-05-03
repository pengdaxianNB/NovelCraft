"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { Tabs } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type { Novel, Character, RagDocument as RagDoc } from "@/types";

export default function SettingsPage() {
  const { id } = useParams<{ id: string }>();
  const [novel, setNovel] = useState<Novel | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [documents, setDocuments] = useState<RagDoc[]>([]);
  const [activeTab, setActiveTab] = useState("basic");
  const [loading, setLoading] = useState(true);

  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");
  const [synopsis, setSynopsis] = useState("");
  const [tone, setTone] = useState("热血");
  const [pov, setPov] = useState("第三人称");
  const [wordsPerChapter, setWordsPerChapter] = useState(3000);
  const [customInstructions, setCustomInstructions] = useState("");

  const [showCharDialog, setShowCharDialog] = useState(false);
  const [charForm, setCharForm] = useState({ name: "", role: "配角", profile: "{}" });

  const fetchData = async () => {
    const [n, c, d] = await Promise.all([api.getNovel(id), api.listCharacters(id), api.listDocuments(id)]);
    setNovel(n); setCharacters(c); setDocuments(d);
    setTitle(n.title); setGenre(n.genre); setSynopsis(n.synopsis || "");
    if (n.style_config) {
      setTone(n.style_config.tone || "热血");
      setPov(n.style_config.pov || "第三人称");
      setWordsPerChapter(n.style_config.words_per_chapter || 3000);
      setCustomInstructions(n.style_config.custom_instructions || "");
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [id]);

  const handleSaveBasic = async () => {
    await api.updateNovel(id, { title, genre, synopsis });
    alert("已保存");
  };

  const handleSaveStyle = async () => {
    await api.updateNovelStyle(id, { tone, pov, words_per_chapter: wordsPerChapter, custom_instructions: customInstructions });
    alert("已保存");
  };

  const handleCreateCharacter = async () => {
    let profile = {};
    try { profile = JSON.parse(charForm.profile); } catch { profile = { description: charForm.profile }; }
    await api.createCharacter(id, { name: charForm.name, role: charForm.role, profile });
    setShowCharDialog(false);
    setCharForm({ name: "", role: "配角", profile: "{}" });
    fetchData();
  };

  const handleDeleteCharacter = async (charId: string) => {
    await api.deleteCharacter(charId);
    fetchData();
  };

  const handleUploadDocument = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    await api.uploadDocument(id, formData);
    fetchData();
  };

  if (loading) return <main className="p-8"><p className="text-muted-foreground">加载中...</p></main>;

  const tabs = [
    { key: "basic", label: "基础信息" },
    { key: "style", label: "写作风格" },
    { key: "characters", label: "角色管理" },
    { key: "world", label: "世界观" },
    { key: "knowledge", label: "知识库" },
  ];

  return (
    <main className="p-8">
      <h1 className="text-3xl font-bold text-foreground mb-6">设定工坊</h1>

      <Tabs tabs={tabs} active={activeTab} onChange={setActiveTab}>
        {activeTab === "basic" && (
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col gap-4 max-w-md">
                <div><label className="block text-sm font-medium mb-1">书名</label><input className="w-full px-3 py-2 border border-border rounded-md bg-background" value={title} onChange={e => setTitle(e.target.value)} /></div>
                <div><label className="block text-sm font-medium mb-1">题材</label><select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={genre} onChange={e => setGenre(e.target.value)}>{["玄幻","都市","言情","仙侠","科幻","悬疑","历史","游戏"].map(g => <option key={g} value={g}>{g}</option>)}</select></div>
                <div><label className="block text-sm font-medium mb-1">简介</label><textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={3} value={synopsis} onChange={e => setSynopsis(e.target.value)} /></div>
                <Button onClick={handleSaveBasic}>保存基础信息</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "style" && (
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col gap-4 max-w-md">
                <div><label className="block text-sm font-medium mb-1">文风</label><select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={tone} onChange={e => setTone(e.target.value)}>{["轻松","严肃","幽默","热血"].map(t => <option key={t} value={t}>{t}</option>)}</select></div>
                <div><label className="block text-sm font-medium mb-1">视角</label><select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={pov} onChange={e => setPov(e.target.value)}>{["第一人称","第三人称","混合"].map(p => <option key={p} value={p}>{p}</option>)}</select></div>
                <div><label className="block text-sm font-medium mb-1">每章默认字数</label><input type="number" className="w-full px-3 py-2 border border-border rounded-md bg-background" value={wordsPerChapter} onChange={e => setWordsPerChapter(Number(e.target.value))} /></div>
                <div><label className="block text-sm font-medium mb-1">自定义写作指令</label><textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={4} value={customInstructions} onChange={e => setCustomInstructions(e.target.value)} /></div>
                <Button onClick={handleSaveStyle}>保存风格设定</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "characters" && (
          <div>
            <div className="flex items-center justify-between mb-4"><h3 className="font-semibold">角色列表</h3><Button onClick={() => setShowCharDialog(true)}>+ 添加角色</Button></div>
            <Dialog open={showCharDialog} onClose={() => setShowCharDialog(false)} title="添加角色">
              <div className="flex flex-col gap-4">
                <div><label className="block text-sm font-medium mb-1">名称</label><input className="w-full px-3 py-2 border border-border rounded-md bg-background" value={charForm.name} onChange={e => setCharForm({ ...charForm, name: e.target.value })} /></div>
                <div><label className="block text-sm font-medium mb-1">角色定位</label><select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={charForm.role} onChange={e => setCharForm({ ...charForm, role: e.target.value })}>{["主角","配角","反派","路人"].map(r => <option key={r} value={r}>{r}</option>)}</select></div>
                <div><label className="block text-sm font-medium mb-1">档案 (JSON格式)</label><textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={4} value={charForm.profile} onChange={e => setCharForm({ ...charForm, profile: e.target.value })} /></div>
                <Button onClick={handleCreateCharacter}>添加</Button>
              </div>
            </Dialog>
            {characters.length === 0 ? <p className="text-muted-foreground">暂无角色</p> : (
              <div className="grid grid-cols-3 gap-4">
                {characters.map(c => (
                  <Card key={c.id}><CardHeader><div className="flex items-center justify-between"><h4 className="font-semibold">{c.name}</h4><Badge variant={c.role}>{c.role}</Badge></div></CardHeader><CardContent><pre className="text-xs text-muted-foreground truncate">{JSON.stringify(c.profile)}</pre><Button variant="destructive" size="sm" className="mt-2" onClick={() => handleDeleteCharacter(c.id)}>删除</Button></CardContent></Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "knowledge" && (
          <div>
            <div className="flex items-center justify-between mb-4"><h3 className="font-semibold">知识库文档</h3><input type="file" onChange={handleUploadDocument} className="text-sm" /></div>
            {documents.length === 0 ? <p className="text-muted-foreground">暂无文档，上传参考资料（修炼体系、历史考据等）</p> : (
              <div className="space-y-2">
                {documents.map(d => (
                  <Card key={d.id}><CardContent className="p-4 flex items-center justify-between"><div><span className="font-medium">{d.filename}</span><span className="text-sm text-muted-foreground ml-4">{d.chunk_count} 个分块 · {d.status}</span></div><Button variant="destructive" size="sm" onClick={() => { api.deleteDocument(d.id); fetchData(); }}>删除</Button></CardContent></Card>
                ))}
              </div>
            )}
          </div>
        )}
      </Tabs>
    </main>
  );
}
