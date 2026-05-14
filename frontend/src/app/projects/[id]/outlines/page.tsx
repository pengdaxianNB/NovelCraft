"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { api } from "@/lib/api";
import type { Outline } from "@/types";

const levelLabel: Record<string, string> = { volume: "卷", arc: "弧", chapter: "章" };
const statusLabel: Record<string, string> = { planned: "规划中", writing: "写作中", done: "已完成" };

function flattenTree(nodes: Outline[], result: Outline[] = []): Outline[] {
  for (const n of nodes) {
    result.push(n);
    if (n.children?.length) flattenTree(n.children, result);
  }
  return result;
}

function findNode(nodes: Outline[], id: string): Outline | null {
  for (const n of nodes) {
    if (n.id === id) return n;
    if (n.children?.length) {
      const found = findNode(n.children, id);
      if (found) return found;
    }
  }
  return null;
}

export default function OutlinesPage() {
  const { id } = useParams<{ id: string }>();
  const [outlines, setOutlines] = useState<Outline[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  // Edit form
  const [editTitle, setEditTitle] = useState("");
  const [editSummary, setEditSummary] = useState("");
  const [editStatus, setEditStatus] = useState("planned");
  const [dirty, setDirty] = useState(false);

  // Create dialog
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ level: "chapter", parent_id: "", title: "", summary: "" });

  const fetchOutlines = async () => {
    try {
      const data = await api.listOutlines(id);
      setOutlines(data || []);
      setExpandedIds(new Set(flattenTree(data || []).map((o) => o.id)));
    } catch (e: any) {
      setError(e.message || "加载大纲失败");
    }
    setLoading(false);
  };

  useEffect(() => { fetchOutlines(); }, [id]);

  const flatList = flattenTree(outlines);
  const selected = selectedId ? findNode(outlines, selectedId) : null;

  useEffect(() => {
    if (selected) {
      setEditTitle(selected.title);
      setEditSummary(selected.summary || "");
      setEditStatus(selected.status);
      setDirty(false);
    }
  }, [selectedId]);

  const handleSelect = (oid: string) => {
    if (dirty && !window.confirm("有未保存的修改，是否放弃？")) return;
    setSelectedId(oid);
  };

  const handleSave = async () => {
    if (!selected) return;
    await api.updateOutline(selected.id, { title: editTitle, summary: editSummary, status: editStatus });
    setDirty(false);
    fetchOutlines();
  };

  const handleDelete = async () => {
    if (!selected) return;
    if (!window.confirm(`确定删除大纲「${selected.title}」吗？其子节点也将被删除。`)) return;
    await api.deleteOutline(selected.id);
    setSelectedId(null);
    setDirty(false);
    fetchOutlines();
  };

  const handleCreate = async () => {
    await api.createOutline(id, {
      level: createForm.level,
      parent_id: createForm.parent_id || null,
      sequence: 0,
      title: createForm.title,
      summary: createForm.summary || null,
    });
    setShowCreate(false);
    setCreateForm({ level: "chapter", parent_id: "", title: "", summary: "" });
    fetchOutlines();
  };

  const handleMove = async (direction: "up" | "down") => {
    if (!selected) return;
    const siblings = flatList.filter((o) => o.parent_id === selected.parent_id).sort((a, b) => a.sequence - b.sequence);
    const idx = siblings.findIndex((o) => o.id === selected.id);
    if (idx === -1) return;
    const targetIdx = direction === "up" ? idx - 1 : idx + 1;
    if (targetIdx < 0 || targetIdx >= siblings.length) return;
    const target = siblings[targetIdx];
    await api.reorderOutline(selected.id, { new_sequence: target.sequence, new_parent_id: selected.parent_id });
    await api.reorderOutline(target.id, { new_sequence: selected.sequence, new_parent_id: target.parent_id });
    fetchOutlines();
  };

  const toggleExpand = (oid: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(oid)) next.delete(oid); else next.add(oid);
      return next;
    });
  };

  if (loading) return <main className="p-8"><p className="text-muted-foreground">加载中...</p></main>;
  if (error) return <main className="p-8"><p className="text-red-600">出错了：{error}</p></main>;

  const parentOptions = flatList.filter((o) => o.id !== selectedId);

  return (
    <div className="flex h-full">
      {/* Left: tree */}
      <aside className="w-72 border-r border-border p-4 overflow-y-auto">
        <div className="flex items-center justify-between mb-3">
          <h3 className="font-semibold">大纲树</h3>
          <Button size="sm" onClick={() => setShowCreate(true)}>+ 新建</Button>
        </div>
        {outlines.length === 0 ? (
          <p className="text-sm text-muted-foreground">暂无大纲，点击"新建"创建</p>
        ) : (
          <OutlineTreeView
            nodes={outlines}
            depth={0}
            selectedId={selectedId}
            expandedIds={expandedIds}
            onSelect={handleSelect}
            onToggle={toggleExpand}
          />
        )}
      </aside>

      {/* Right: detail */}
      <main className="flex-1 p-8">
        {!selected ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-muted-foreground">选择左侧大纲节点查看和编辑详情</p>
          </div>
        ) : (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">
                <Badge variant={selected.level} className="mr-2">{levelLabel[selected.level] || selected.level}</Badge>
                {selected.title}
              </h2>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => handleMove("up")}>↑ 上移</Button>
                <Button variant="outline" size="sm" onClick={() => handleMove("down")}>↓ 下移</Button>
                <Button variant="outline" size="sm" onClick={() => { setCreateForm({ level: "chapter", parent_id: selected.id, title: "", summary: "" }); setShowCreate(true); }}>+ 子节点</Button>
                <Button variant="destructive" size="sm" onClick={handleDelete}>删除</Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-6 space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">标题</label>
                  <input className="w-full px-3 py-2 border border-border rounded-md bg-background" value={editTitle} onChange={(e) => { setEditTitle(e.target.value); setDirty(true); }} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">摘要</label>
                  <textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={6} value={editSummary} onChange={(e) => { setEditSummary(e.target.value); setDirty(true); }} />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">状态</label>
                  <select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={editStatus} onChange={(e) => { setEditStatus(e.target.value); setDirty(true); }}>
                    {Object.entries(statusLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <Button onClick={handleSave} disabled={!dirty}>保存修改</Button>
              </CardContent>
            </Card>

            <Card className="mt-4">
              <CardContent className="p-4 text-sm text-muted-foreground">
                <p>层级：{levelLabel[selected.level] || selected.level} · 排序号：{selected.sequence} · 状态：{statusLabel[selected.status] || selected.status}</p>
                {selected.parent_id && <p className="mt-1">父节点 ID：{selected.parent_id}</p>}
                <p className="mt-1">子节点数：{selected.children?.length || 0}</p>
              </CardContent>
            </Card>
          </div>
        )}
      </main>

      {/* Create dialog */}
      <Dialog open={showCreate} onClose={() => setShowCreate(false)} title="新建大纲">
        <div className="flex flex-col gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">层级</label>
            <select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={createForm.level} onChange={(e) => setCreateForm({ ...createForm, level: e.target.value })}>
              {Object.entries(levelLabel).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">父节点（可选）</label>
            <select className="w-full px-3 py-2 border border-border rounded-md bg-background" value={createForm.parent_id} onChange={(e) => setCreateForm({ ...createForm, parent_id: e.target.value })}>
              <option value="">-- 无（根节点）--</option>
              {parentOptions.map((o) => <option key={o.id} value={o.id}>{levelLabel[o.level] || o.level}: {o.title}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">标题</label>
            <input className="w-full px-3 py-2 border border-border rounded-md bg-background" value={createForm.title} onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })} placeholder="大纲标题" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">摘要</label>
            <textarea className="w-full px-3 py-2 border border-border rounded-md bg-background" rows={3} value={createForm.summary} onChange={(e) => setCreateForm({ ...createForm, summary: e.target.value })} placeholder="简要描述..." />
          </div>
          <Button onClick={handleCreate} disabled={!createForm.title}>创建</Button>
        </div>
      </Dialog>
    </div>
  );
}

function OutlineTreeView({
  nodes,
  depth,
  selectedId,
  expandedIds,
  onSelect,
  onToggle,
}: {
  nodes: Outline[];
  depth: number;
  selectedId: string | null;
  expandedIds: Set<string>;
  onSelect: (id: string) => void;
  onToggle: (id: string) => void;
}) {
  return (
    <ul className={`space-y-0.5 ${depth > 0 ? "ml-4" : ""}`}>
      {nodes.map((o) => {
        const hasChildren = o.children?.length > 0;
        const isExpanded = expandedIds.has(o.id);
        const isSelected = selectedId === o.id;
        return (
          <li key={o.id}>
            <div
              className={`flex items-center gap-1 py-1 px-1.5 rounded cursor-pointer text-sm transition-colors ${
                isSelected ? "bg-primary/10 text-primary font-medium" : "hover:bg-muted"
              }`}
              onClick={() => onSelect(o.id)}
            >
              {hasChildren ? (
                <button
                  className="w-4 h-4 flex items-center justify-center text-xs text-muted-foreground hover:text-foreground"
                  onClick={(e) => { e.stopPropagation(); onToggle(o.id); }}
                >
                  {isExpanded ? "▾" : "▸"}
                </button>
              ) : (
                <span className="w-4" />
              )}
              <Badge variant={o.level} className="text-[10px] px-1 py-0">{levelLabel[o.level] || o.level}</Badge>
              <span className="truncate">{o.title}</span>
            </div>
            {hasChildren && isExpanded && (
              <OutlineTreeView nodes={o.children!} depth={depth + 1} selectedId={selectedId} expandedIds={expandedIds} onSelect={onSelect} onToggle={onToggle} />
            )}
          </li>
        );
      })}
    </ul>
  );
}
