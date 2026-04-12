export interface Session {
  id: string;
  title: string;
  knowledge_base_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'human' | 'ai' | 'system';
  content: string;
  created_at: string;
}

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  created_at: string;
  document_count: number;
  documents: DocumentInfo[];
}

export interface DocumentInfo {
  id: number;
  filename: string;
  file_type: string;
  chunk_count: number;
}

export interface LogEntry {
  id: number;
  level: string;
  module: string;
  action: string;
  detail: string;
  created_at: string;
}
