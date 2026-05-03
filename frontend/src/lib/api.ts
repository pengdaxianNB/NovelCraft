const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  listNovels: () => request<any[]>("/novels"),
  createNovel: (data: any) => request("/novels", { method: "POST", body: JSON.stringify(data) }),
  getNovel: (id: string) => request(`/novels/${id}`),
  updateNovel: (id: string, data: any) => request(`/novels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteNovel: (id: string) => request(`/novels/${id}`, { method: "DELETE" }),
  updateNovelStyle: (id: string, data: any) => request(`/novels/${id}/style`, { method: "PATCH", body: JSON.stringify(data) }),

  listChapters: (novelId: string) => request(`/novels/${novelId}/chapters`),
  getChapter: (id: string) => request(`/chapters/${id}`),
  updateChapter: (id: string, data: any) => request(`/chapters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  publishChapter: (id: string) => request(`/chapters/${id}/publish`, { method: "POST" }),
  rewriteChapter: (id: string) => request(`/chapters/${id}/rewrite`, { method: "POST" }),

  generateOutline: (novelId: string, data: any) => request(`/novels/${novelId}/generate/outline`, { method: "POST", body: JSON.stringify(data) }),
  generateChapter: (novelId: string, data: any) => request(`/novels/${novelId}/generate/chapter`, { method: "POST", body: JSON.stringify(data) }),
  getTaskStatus: (taskId: string) => request(`/generation/tasks/${taskId}`),
  listTasks: () => request("/generation/tasks"),
  cancelTask: (taskId: string) => request(`/generation/tasks/${taskId}/cancel`, { method: "POST" }),
  getStreamUrl: (taskId: string) => `${BASE}/generation/stream/${taskId}`,

  listCharacters: (novelId: string) => request(`/novels/${novelId}/characters`),
  createCharacter: (novelId: string, data: any) => request(`/novels/${novelId}/characters`, { method: "POST", body: JSON.stringify(data) }),
  updateCharacter: (id: string, data: any) => request(`/characters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCharacter: (id: string) => request(`/characters/${id}`, { method: "DELETE" }),

  listWorldSettings: (novelId: string) => request(`/novels/${novelId}/world-settings`),
  createWorldSetting: (novelId: string, data: any) => request(`/novels/${novelId}/world-settings`, { method: "POST", body: JSON.stringify(data) }),
  updateWorldSetting: (id: string, data: any) => request(`/world-settings/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteWorldSetting: (id: string) => request(`/world-settings/${id}`, { method: "DELETE" }),

  listOutlines: (novelId: string) => request(`/novels/${novelId}/outlines`),
  createOutline: (novelId: string, data: any) => request(`/novels/${novelId}/outlines`, { method: "POST", body: JSON.stringify(data) }),
  updateOutline: (id: string, data: any) => request(`/outlines/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteOutline: (id: string) => request(`/outlines/${id}`, { method: "DELETE" }),
  reorderOutline: (id: string, data: any) => request(`/outlines/${id}/reorder`, { method: "PATCH", body: JSON.stringify(data) }),

  listDocuments: (novelId: string) => request(`/novels/${novelId}/rag/documents`),
  deleteDocument: (id: string) => request(`/rag/documents/${id}`, { method: "DELETE" }),
  uploadDocument: (novelId: string, formData: FormData) =>
    fetch(`${BASE}/novels/${novelId}/rag/documents`, { method: "POST", body: formData }).then((r) => r.json()),
};
