export interface Novel {
  id: string;
  title: string;
  genre: string;
  synopsis: string | null;
  style_config: Record<string, any>;
  schedule_config: Record<string, any>;
  status: string;
  created_at: string;
  updated_at: string;
  chapter_count: number;
  published_count: number;
}

export interface Chapter {
  id: string;
  novel_id: string;
  outline_id: string | null;
  chapter_number: number;
  title: string;
  content: string | null;
  word_count: number;
  status: "draft" | "review" | "published";
  generation_meta: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Character {
  id: string;
  novel_id: string;
  name: string;
  role: string;
  profile: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Outline {
  id: string;
  novel_id: string;
  level: string;
  parent_id: string | null;
  sequence: number;
  title: string;
  summary: string | null;
  status: string;
  children: Outline[];
  created_at: string;
  updated_at: string;
}

export interface GenerationTask {
  id: string;
  novel_id: string;
  task_type: string;
  target_id: string | null;
  status: string;
  progress: Record<string, any>;
  result: Record<string, any>;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}
