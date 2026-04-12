const BASE_URL = 'http://localhost:8000';

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, options);
  return res.json();
}

// Sessions
export const sessionsApi = {
  list: () => request<any[]>('/api/sessions'),
  create: (title?: string, knowledge_base_id?: string | null) =>
    request<any>('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title || 'New Chat', knowledge_base_id: knowledge_base_id || null }),
    }),
  getMessages: (sessionId: string) => request<any[]>(`/api/sessions/${sessionId}/messages`),
  update: (sessionId: string, data: { title?: string; knowledge_base_id?: string | null }) =>
    request<any>(`/api/sessions/${sessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),
  delete: (sessionId: string) =>
    request<any>(`/api/sessions/${sessionId}`, { method: 'DELETE' }),
};

// Chat (SSE stream)
export function chatStream(
  sessionId: string,
  message: string,
  onChunk: (text: string) => void,
  onDone: () => void,
) {
  fetch(`${BASE_URL}/api/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  }).then(async (res) => {
    const reader = res.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            onDone();
            return;
          }
          onChunk(data);
        }
      }
    }
    onDone();
  });
}

// Knowledge
export const knowledgeApi = {
  list: () => request<any[]>('/api/knowledge'),
  create: (name: string, description?: string) => {
    const form = new FormData();
    form.append('name', name);
    if (description) form.append('description', description);
    return request<any>('/api/knowledge', { method: 'POST', body: form });
  },
  upload: (kbId: string, file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<any>(`/api/knowledge/${kbId}/upload`, { method: 'POST', body: form });
  },
  delete: (kbId: string) =>
    request<any>(`/api/knowledge/${kbId}`, { method: 'DELETE' }),
};

// Logs
export const logsApi = {
  list: (params?: { module?: string; level?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.module) query.set('module', params.module);
    if (params?.level) query.set('level', params.level);
    if (params?.limit) query.set('limit', String(params.limit));
    if (params?.offset) query.set('offset', String(params.offset));
    return request<any[]>(`/api/logs?${query.toString()}`);
  },
};
