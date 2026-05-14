import type {
  Chapter,
  ChapterReviewResult,
  Character,
  GenerateChapterResult,
  GenerateOutlineResult,
  GenerationTask,
  Novel,
  Outline,
  RagDocument,
  WorldSetting,
  WorldSettingConsistencyResult,
} from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const ACCESS_TOKEN = process.env.NEXT_PUBLIC_ACCESS_TOKEN || "";

function authHeaders(): HeadersInit {
  return ACCESS_TOKEN ? { Authorization: `Bearer ${ACCESS_TOKEN}` } : {};
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      headers: { "Content-Type": "application/json", ...authHeaders(), ...options?.headers },
      ...options,
    });
  } catch (e: any) {
    throw new Error(e.message || "网络连接失败，请检查后端服务是否已启动");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  try {
    return await res.json();
  } catch {
    throw new Error("API返回数据格式异常");
  }
}

export const api = {
  listNovels: () => request<Novel[]>("/novels"),
  createNovel: (data: any) => request<Novel>("/novels", { method: "POST", body: JSON.stringify(data) }),
  getNovel: (id: string) => request<Novel>(`/novels/${id}`),
  updateNovel: (id: string, data: any) => request<Novel>(`/novels/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteNovel: (id: string) => request(`/novels/${id}`, { method: "DELETE" }),
  updateNovelStyle: (id: string, data: any) => request<Novel>(`/novels/${id}/style`, { method: "PATCH", body: JSON.stringify(data) }),

  listChapters: (novelId: string) => request<Chapter[]>(`/novels/${novelId}/chapters`),
  getChapter: (id: string) => request<Chapter>(`/chapters/${id}`),
  updateChapter: (id: string, data: any) => request<Chapter>(`/chapters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  publishChapter: (id: string) => request<Chapter>(`/chapters/${id}/publish`, { method: "POST" }),
  reviewChapter: (id: string, data: any) => request<ChapterReviewResult>(`/chapters/${id}/review`, { method: "POST", body: JSON.stringify(data) }),
  rewriteChapter: (id: string) => request(`/chapters/${id}/rewrite`, { method: "POST" }),

  generateOutline: (novelId: string, data: any) => request<GenerateOutlineResult>(`/novels/${novelId}/generate/outline`, { method: "POST", body: JSON.stringify(data) }),
  generateChapter: (novelId: string, data: any) => request<GenerateChapterResult>(`/novels/${novelId}/generate/chapter`, { method: "POST", body: JSON.stringify(data) }),
  getTaskStatus: (taskId: string) => request<GenerationTask>(`/generation/tasks/${taskId}`),
  listTasks: () => request<GenerationTask[]>("/generation/tasks"),
  cancelTask: (taskId: string) => request(`/generation/tasks/${taskId}/cancel`, { method: "POST" }),
  getStreamUrl: (taskId: string) => {
    const url = new URL(`${BASE}/generation/stream/${taskId}`);
    if (ACCESS_TOKEN) url.searchParams.set("access_token", ACCESS_TOKEN);
    return url.toString();
  },

  listCharacters: (novelId: string) => request<Character[]>(`/novels/${novelId}/characters`),
  createCharacter: (novelId: string, data: any) => request<Character>(`/novels/${novelId}/characters`, { method: "POST", body: JSON.stringify(data) }),
  updateCharacter: (id: string, data: any) => request<Character>(`/characters/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteCharacter: (id: string) => request(`/characters/${id}`, { method: "DELETE" }),

  listWorldSettings: (novelId: string) => request<WorldSetting[]>(`/novels/${novelId}/world-settings`),
  createWorldSetting: (novelId: string, data: any) => request<WorldSetting>(`/novels/${novelId}/world-settings`, { method: "POST", body: JSON.stringify(data) }),
  checkWorldSetting: (novelId: string, data: any) => request<WorldSettingConsistencyResult>(`/novels/${novelId}/world-settings/check`, { method: "POST", body: JSON.stringify(data) }),
  updateWorldSetting: (id: string, data: any) => request<WorldSetting>(`/world-settings/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteWorldSetting: (id: string) => request(`/world-settings/${id}`, { method: "DELETE" }),

  listOutlines: (novelId: string) => request<Outline[]>(`/novels/${novelId}/outlines`),
  createOutline: (novelId: string, data: any) => request<Outline>(`/novels/${novelId}/outlines`, { method: "POST", body: JSON.stringify(data) }),
  updateOutline: (id: string, data: any) => request<Outline>(`/outlines/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteOutline: (id: string) => request(`/outlines/${id}`, { method: "DELETE" }),
  reorderOutline: (id: string, data: any) => request(`/outlines/${id}/reorder`, { method: "PATCH", body: JSON.stringify(data) }),

  listDocuments: (novelId: string) => request<RagDocument[]>(`/novels/${novelId}/rag/documents`),
  deleteDocument: (id: string) => request(`/rag/documents/${id}`, { method: "DELETE" }),
  uploadDocument: (novelId: string, formData: FormData) =>
    fetch(`${BASE}/novels/${novelId}/rag/documents`, { method: "POST", headers: authHeaders(), body: formData }).then((r) => r.json()),
};
