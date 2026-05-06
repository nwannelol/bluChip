const API = process.env.NEXT_PUBLIC_API_URL ?? '';
const ADMIN_KEY = process.env.NEXT_PUBLIC_ADMIN_KEY ?? '';

const adminHeaders = {
  'Content-Type': 'application/json',
  'X-Admin-Key': ADMIN_KEY,
};

/* ── Streaming chat ──────────────────────────────────────────────── */

export async function streamChat(
  message: string,
  agent: string,
  sessionId: string,
  onToken: (t: string) => void,
  onDone: () => void,
  onError: (e: Error) => void,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch(`${API}/api/v1/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, agent, session_id: sessionId, channel: 'web' }),
    });
  } catch (e) {
    onError(e instanceof Error ? e : new Error('Network error'));
    return;
  }

  if (!res.ok || !res.body) {
    onError(new Error(`HTTP ${res.status}`));
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() ?? '';
      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        const data = line.slice(6);
        if (data === '[DONE]') { onDone(); return; }
        if (data) onToken(data);
      }
    }
    onDone();
  } catch (e) {
    onError(e instanceof Error ? e : new Error('Stream error'));
  } finally {
    reader.releaseLock();
  }
}

/* ── Analytics / admin ───────────────────────────────────────────── */

export interface AgentInfo {
  name: string;
  display_name: string;
  description: string;
  status: 'active' | 'stub';
  is_stub: boolean;
}

export interface AnalyticsSummary {
  total_conversations: number;
  total_messages: number;
  total_fans: number;
  messages_today: number;
  channels: Record<string, number>;
}

export interface LogEntry {
  id: string;
  agent_name: string;
  session_id: string;
  action: string;
  duration_ms: number | null;
  error: string | null;
  created_at: string;
}

export async function fetchAgents(): Promise<AgentInfo[]> {
  const res = await fetch(`${API}/api/v1/admin/agents`, { headers: adminHeaders });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchSummary(): Promise<AnalyticsSummary> {
  const res = await fetch(`${API}/api/v1/analytics/summary`, { headers: adminHeaders });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function fetchLogs(limit = 50): Promise<LogEntry[]> {
  const res = await fetch(`${API}/api/v1/admin/logs?limit=${limit}`, { headers: adminHeaders });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function triggerKnowledgeRefresh(): Promise<void> {
  await fetch(`${API}/api/v1/admin/knowledge/refresh`, {
    method: 'POST',
    headers: adminHeaders,
  });
}
