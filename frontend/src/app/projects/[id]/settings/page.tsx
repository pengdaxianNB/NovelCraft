"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Tabs } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import type {
  Character,
  Novel,
  RagDocument,
  WorldSetting,
  WorldSettingConsistencyResult,
} from "@/types";

const fieldClass = "w-full px-3 py-2 border border-border rounded-md bg-background";

export default function SettingsPage() {
  const { id } = useParams<{ id: string }>();
  const [novel, setNovel] = useState<Novel | null>(null);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [worldSettings, setWorldSettings] = useState<WorldSetting[]>([]);
  const [documents, setDocuments] = useState<RagDocument[]>([]);
  const [activeTab, setActiveTab] = useState("basic");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [genre, setGenre] = useState("");
  const [synopsis, setSynopsis] = useState("");
  const [tone, setTone] = useState("热血");
  const [pov, setPov] = useState("第三人称");
  const [wordsPerChapter, setWordsPerChapter] = useState(3000);
  const [customInstructions, setCustomInstructions] = useState("");

  const [showCharDialog, setShowCharDialog] = useState(false);
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);
  const [charForm, setCharForm] = useState({ name: "", role: "配角", profile: "{}" });

  const [showWorldDialog, setShowWorldDialog] = useState(false);
  const [editingWorld, setEditingWorld] = useState<WorldSetting | null>(null);
  const [worldForm, setWorldForm] = useState({ category: "地理", title: "", content: "" });
  const [checkingWorld, setCheckingWorld] = useState(false);
  const [worldCheck, setWorldCheck] = useState<WorldSettingConsistencyResult | null>(null);
  const [worldCheckError, setWorldCheckError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      const [n, c, w, d] = await Promise.all([
        api.getNovel(id),
        api.listCharacters(id),
        api.listWorldSettings(id),
        api.listDocuments(id),
      ]);
      setNovel(n);
      setCharacters(c);
      setWorldSettings(w);
      setDocuments(d);
      setTitle(n.title);
      setGenre(n.genre);
      setSynopsis(n.synopsis || "");
      setTone(n.style_config?.tone || "热血");
      setPov(n.style_config?.pov || "第三人称");
      setWordsPerChapter(n.style_config?.words_per_chapter || 3000);
      setCustomInstructions(n.style_config?.custom_instructions || "");
      setError(null);
    } catch (e: any) {
      setError(e.message || "加载失败，请检查后端服务是否已启动");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const resetCharacterDialog = () => {
    setShowCharDialog(false);
    setEditingCharacter(null);
    setCharForm({ name: "", role: "配角", profile: "{}" });
  };

  const resetWorldDialog = () => {
    setShowWorldDialog(false);
    setEditingWorld(null);
    setWorldForm({ category: "地理", title: "", content: "" });
    setWorldCheck(null);
    setWorldCheckError(null);
  };

  const handleSaveBasic = async () => {
    await api.updateNovel(id, { title, genre, synopsis });
    alert("已保存");
  };

  const handleSaveStyle = async () => {
    await api.updateNovelStyle(id, {
      tone,
      pov,
      words_per_chapter: wordsPerChapter,
      custom_instructions: customInstructions,
    });
    alert("已保存");
  };

  const handleSaveCharacter = async () => {
    let profile = {};
    try {
      profile = JSON.parse(charForm.profile);
    } catch {
      profile = { description: charForm.profile };
    }

    if (editingCharacter) {
      await api.updateCharacter(editingCharacter.id, {
        name: charForm.name,
        role: charForm.role,
        profile,
      });
    } else {
      await api.createCharacter(id, { name: charForm.name, role: charForm.role, profile });
    }
    resetCharacterDialog();
    fetchData();
  };

  const openEditCharacter = (character: Character) => {
    setEditingCharacter(character);
    setCharForm({
      name: character.name,
      role: character.role,
      profile: JSON.stringify(character.profile, null, 2),
    });
    setShowCharDialog(true);
  };

  const handleCheckWorldSetting = async () => {
    setCheckingWorld(true);
    setWorldCheckError(null);
    try {
      const result = await api.checkWorldSetting(id, worldForm);
      setWorldCheck(result);
    } catch (e: any) {
      setWorldCheckError(e.message || "一致性检查失败");
    } finally {
      setCheckingWorld(false);
    }
  };

  const handleSaveWorldSetting = async () => {
    if (editingWorld) {
      await api.updateWorldSetting(editingWorld.id, worldForm);
    } else {
      await api.createWorldSetting(id, worldForm);
    }
    resetWorldDialog();
    fetchData();
  };

  const openEditWorld = (setting: WorldSetting) => {
    setEditingWorld(setting);
    setWorldForm({
      category: setting.category,
      title: setting.title,
      content: setting.content,
    });
    setWorldCheck(null);
    setWorldCheckError(null);
    setShowWorldDialog(true);
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
  if (error) return <main className="p-8"><p className="text-red-600">出错了：{error}</p></main>;

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
                <Field label="书名"><input className={fieldClass} value={title} onChange={(e) => setTitle(e.target.value)} /></Field>
                <Field label="题材">
                  <select className={fieldClass} value={genre} onChange={(e) => setGenre(e.target.value)}>
                    {["玄幻", "都市", "言情", "仙侠", "科幻", "悬疑", "历史", "游戏"].map((g) => <option key={g} value={g}>{g}</option>)}
                  </select>
                </Field>
                <Field label="简介"><textarea className={fieldClass} rows={3} value={synopsis} onChange={(e) => setSynopsis(e.target.value)} /></Field>
                <Button onClick={handleSaveBasic}>保存基础信息</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "style" && (
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col gap-4 max-w-md">
                <Field label="文风">
                  <select className={fieldClass} value={tone} onChange={(e) => setTone(e.target.value)}>
                    {["轻松", "严肃", "幽默", "热血"].map((t) => <option key={t} value={t}>{t}</option>)}
                  </select>
                </Field>
                <Field label="视角">
                  <select className={fieldClass} value={pov} onChange={(e) => setPov(e.target.value)}>
                    {["第一人称", "第三人称", "混合"].map((p) => <option key={p} value={p}>{p}</option>)}
                  </select>
                </Field>
                <Field label="每章默认字数"><input type="number" className={fieldClass} value={wordsPerChapter} onChange={(e) => setWordsPerChapter(Number(e.target.value))} /></Field>
                <Field label="自定义写作指令"><textarea className={fieldClass} rows={4} value={customInstructions} onChange={(e) => setCustomInstructions(e.target.value)} /></Field>
                <Button onClick={handleSaveStyle}>保存风格设定</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === "characters" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">角色列表</h3>
              <Button onClick={() => setShowCharDialog(true)}>+ 添加角色</Button>
            </div>
            <Dialog open={showCharDialog} onClose={resetCharacterDialog} title={editingCharacter ? "编辑角色" : "添加角色"}>
              <div className="flex flex-col gap-4">
                <Field label="名称"><input className={fieldClass} value={charForm.name} onChange={(e) => setCharForm({ ...charForm, name: e.target.value })} /></Field>
                <Field label="角色定位">
                  <select className={fieldClass} value={charForm.role} onChange={(e) => setCharForm({ ...charForm, role: e.target.value })}>
                    {["主角", "配角", "反派", "路人", "protagonist", "supporting", "antagonist"].map((r) => <option key={r} value={r}>{r}</option>)}
                  </select>
                </Field>
                <Field label="档案 JSON"><textarea className={`${fieldClass} font-mono`} rows={6} value={charForm.profile} onChange={(e) => setCharForm({ ...charForm, profile: e.target.value })} /></Field>
                <Button onClick={handleSaveCharacter}>{editingCharacter ? "保存" : "添加"}</Button>
              </div>
            </Dialog>
            {characters.length === 0 ? <p className="text-muted-foreground">暂无角色</p> : (
              <div className="grid grid-cols-3 gap-4">
                {characters.map((c) => (
                  <Card key={c.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold">{c.name}</h4>
                        <Badge variant={c.role}>{c.role}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <pre className="text-xs text-muted-foreground whitespace-pre-wrap max-h-32 overflow-auto">{JSON.stringify(c.profile, null, 2)}</pre>
                      <div className="flex gap-2 mt-3">
                        <Button variant="outline" size="sm" onClick={() => openEditCharacter(c)}>编辑</Button>
                        <Button variant="destructive" size="sm" onClick={async () => { await api.deleteCharacter(c.id); fetchData(); }}>删除</Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "world" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">世界观设定</h3>
              <Button onClick={() => setShowWorldDialog(true)}>+ 添加设定</Button>
            </div>
            <Dialog open={showWorldDialog} onClose={resetWorldDialog} title={editingWorld ? "编辑世界观设定" : "添加世界观设定"}>
              <div className="flex flex-col gap-3">
                <Field label="分类">
                  <select className={fieldClass} value={worldForm.category} onChange={(e) => setWorldForm({ ...worldForm, category: e.target.value })}>
                    {["地理", "历史", "势力", "功法", "种族", "法则", "其他"].map((cat) => <option key={cat} value={cat}>{cat}</option>)}
                  </select>
                </Field>
                <Field label="标题"><input className={fieldClass} value={worldForm.title} onChange={(e) => setWorldForm({ ...worldForm, title: e.target.value })} /></Field>
                <Field label="内容"><textarea className={fieldClass} rows={5} value={worldForm.content} onChange={(e) => setWorldForm({ ...worldForm, content: e.target.value })} /></Field>

                {worldCheckError && <p className="text-sm text-red-600">{worldCheckError}</p>}
                {worldCheck && (
                  <div className="rounded-md border border-border p-3 text-sm space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">一致性检查</span>
                      <Badge variant={worldCheck.passed ? "published" : "failed"}>{worldCheck.passed ? "通过" : "需确认"}</Badge>
                    </div>
                    <p>{worldCheck.summary}</p>
                    {worldCheck.issues.map((issue, index) => (
                      <div key={index} className="rounded-md bg-muted p-2">
                        <div className="font-medium">{issue.severity || "提示"}</div>
                        <p>{issue.description}</p>
                        {issue.suggestion && <p className="text-muted-foreground">建议：{issue.suggestion}</p>}
                      </div>
                    ))}
                    <p className="text-xs text-muted-foreground">RAG 命中 {worldCheck.rag_hits.length} 条，用时 {worldCheck.timings_ms.rag_retrieval ?? 0} ms</p>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button variant="outline" onClick={handleCheckWorldSetting} disabled={checkingWorld}>{checkingWorld ? "检查中..." : "RAG 一致性检查"}</Button>
                  <Button onClick={handleSaveWorldSetting}>{editingWorld ? "保存" : "添加"}</Button>
                </div>
              </div>
            </Dialog>
            {worldSettings.length === 0 ? <p className="text-muted-foreground">暂无世界观设定</p> : (
              <div className="space-y-3">
                {worldSettings.map((w) => (
                  <Card key={w.id}>
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div><Badge variant={w.category}>{w.category}</Badge><span className="font-semibold ml-2">{w.title}</span></div>
                        <div className="flex gap-2">
                          <Button variant="outline" size="sm" onClick={() => openEditWorld(w)}>编辑</Button>
                          <Button variant="destructive" size="sm" onClick={async () => { await api.deleteWorldSetting(w.id); fetchData(); }}>删除</Button>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent><p className="text-sm text-muted-foreground whitespace-pre-wrap">{w.content}</p></CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "knowledge" && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">知识库文档</h3>
              <input type="file" onChange={handleUploadDocument} className="text-sm" />
            </div>
            {documents.length === 0 ? <p className="text-muted-foreground">暂无文档</p> : (
              <div className="space-y-2">
                {documents.map((d) => (
                  <Card key={d.id}>
                    <CardContent className="p-4 flex items-center justify-between">
                      <div><span className="font-medium">{d.filename}</span><span className="text-sm text-muted-foreground ml-4">{d.chunk_count} 个分块 · {d.status}</span></div>
                      <Button variant="destructive" size="sm" onClick={async () => { await api.deleteDocument(d.id); fetchData(); }}>删除</Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}
      </Tabs>
    </main>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block text-sm font-medium">
      <span className="block mb-1">{label}</span>
      {children}
    </label>
  );
}
