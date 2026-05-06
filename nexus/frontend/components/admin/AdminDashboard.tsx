'use client';

import { useCallback, useEffect, useState } from 'react';
import {
  fetchAgents,
  fetchLogs,
  fetchSummary,
  triggerKnowledgeRefresh,
  type AgentInfo,
  type AnalyticsSummary,
  type LogEntry,
} from '@/lib/api';
import { ArrowClockwise, Circle } from '@phosphor-icons/react';

export default function AdminDashboard() {
  const [agents, setAgents] = useState<AgentInfo[]>([]);
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [knowledgeMsg, setKnowledgeMsg] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [a, s, l] = await Promise.all([fetchAgents(), fetchSummary(), fetchLogs(40)]);
      setAgents(a);
      setSummary(s);
      setLogs(l);
    } catch {
      // silently retry on next tick
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000);
    return () => clearInterval(interval);
  }, [load]);

  async function handleRefresh() {
    if (refreshing) return;
    setRefreshing(true);
    setKnowledgeMsg(null);
    try {
      await triggerKnowledgeRefresh();
      setKnowledgeMsg('Knowledge refresh started. Check logs in ~60s.');
    } catch {
      setKnowledgeMsg('Refresh failed. Check the backend.');
    } finally {
      setRefreshing(false);
    }
  }

  return (
    <div style={{ minHeight: '100dvh', background: 'var(--color-nx-base)' }}>
      {/* Header */}
      <header
        style={{
          padding: '20px 36px',
          borderBottom: '1px solid var(--color-nx-border)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <a
            href="/"
            style={{
              fontSize: 12,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--color-nx-muted)',
              textDecoration: 'none',
              transition: `color 160ms var(--ease-out)`,
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-nx-text)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-nx-muted)')}
          >
            NEXUS
          </a>
          <span style={{ color: 'var(--color-nx-border)', fontSize: 16 }}>/</span>
          <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--color-nx-text)', letterSpacing: '-0.01em' }}>
            Operations
          </span>
          <span
            style={{
              width: 7,
              height: 7,
              borderRadius: '50%',
              background: 'var(--color-nx-live)',
              display: 'inline-block',
            }}
            className="pulse"
          />
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="pressable"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: '8px 14px',
            borderRadius: 8,
            border: '1px solid var(--color-nx-border)',
            background: 'transparent',
            color: refreshing ? 'var(--color-nx-dim)' : 'var(--color-nx-muted)',
            fontSize: 13,
            cursor: refreshing ? 'not-allowed' : 'pointer',
            transition: `color 180ms var(--ease-out), border-color 180ms var(--ease-out)`,
          }}
          onMouseEnter={e => { if (!refreshing) { e.currentTarget.style.color = 'var(--color-nx-text)'; e.currentTarget.style.borderColor = 'var(--color-nx-blue-dim)'; } }}
          onMouseLeave={e => { e.currentTarget.style.color = refreshing ? 'var(--color-nx-dim)' : 'var(--color-nx-muted)'; e.currentTarget.style.borderColor = 'var(--color-nx-border)'; }}
        >
          <ArrowClockwise
            size={14}
            weight="bold"
            style={{ animation: refreshing ? 'spin 700ms linear infinite' : 'none' }}
          />
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
          Refresh Knowledge
        </button>
      </header>

      {knowledgeMsg && (
        <div style={{ padding: '10px 36px', background: 'var(--color-nx-blue-wash)', borderBottom: '1px solid oklch(72% 0.16 215 / 0.15)', fontSize: 13, color: 'var(--color-nx-blue)' }}>
          {knowledgeMsg}
        </div>
      )}

      <main style={{ padding: '36px', maxWidth: 1200, margin: '0 auto' }}>
        {/* Stats strip */}
        <section style={{ marginBottom: 48 }}>
          <div style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-nx-dim)', marginBottom: 20, fontWeight: 600 }}>
            Overview
          </div>
          <StatStrip summary={summary} loading={loading} />
        </section>

        {/* Two-column: agents left, logs right */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 36, alignItems: 'start' }}>
          {/* Agents */}
          <section>
            <div style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-nx-dim)', marginBottom: 20, fontWeight: 600 }}>
              Agent Status
            </div>
            <AgentGrid agents={agents} loading={loading} />
          </section>

          {/* Logs */}
          <section>
            <div style={{ fontSize: 11, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-nx-dim)', marginBottom: 20, fontWeight: 600 }}>
              Recent Activity
            </div>
            <LogsFeed logs={logs} loading={loading} />
          </section>
        </div>
      </main>
    </div>
  );
}

/* ── Stats strip ─────────────────────────────────────────── */

function StatStrip({ summary, loading }: { summary: AnalyticsSummary | null; loading: boolean }) {
  const stats = [
    { label: 'Conversations', value: summary?.total_conversations },
    { label: 'Messages sent', value: summary?.total_messages },
    { label: 'Fans reached', value: summary?.total_fans },
    { label: 'Today', value: summary?.messages_today },
  ];

  return (
    <div
      className="stagger"
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: 0,
        background: 'var(--color-nx-surface)',
        border: '1px solid var(--color-nx-border)',
        borderRadius: 12,
        overflow: 'hidden',
      }}
    >
      {stats.map((s, i) => (
        <div
          key={s.label}
          style={{
            padding: '24px 28px',
            borderRight: i < stats.length - 1 ? '1px solid var(--color-nx-border)' : 'none',
          }}
        >
          <div
            style={{
              fontSize: 28,
              fontWeight: 700,
              letterSpacing: '-0.04em',
              color: 'var(--color-nx-text)',
              fontVariantNumeric: 'tabular-nums',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {loading ? <SkeletonNum /> : (s.value ?? 0).toLocaleString()}
          </div>
          <div style={{ fontSize: 12, color: 'var(--color-nx-muted)', marginTop: 4 }}>
            {s.label}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Agent grid ──────────────────────────────────────────── */

function AgentGrid({ agents, loading }: { agents: AgentInfo[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {[0, 1, 2, 3].map(i => <SkeletonCard key={i} />)}
      </div>
    );
  }

  return (
    <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {agents.map(a => <AgentRow key={a.name} agent={a} />)}
    </div>
  );
}

function AgentRow({ agent: a }: { agent: AgentInfo }) {
  const live = !a.is_stub;
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        padding: '14px 16px',
        background: 'var(--color-nx-surface)',
        border: '1px solid var(--color-nx-border)',
        borderRadius: 10,
      }}
    >
      <Circle
        size={9}
        weight="fill"
        style={{ color: live ? 'var(--color-nx-live)' : 'var(--color-nx-dim)', flexShrink: 0 }}
      />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-nx-text)' }}>
          {a.display_name}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-nx-muted)', marginTop: 2 }}>
          {a.description}
        </div>
      </div>
      <span
        style={{
          fontSize: 10,
          letterSpacing: '0.06em',
          textTransform: 'uppercase',
          padding: '3px 7px',
          borderRadius: 4,
          fontWeight: 600,
          background: live ? 'oklch(70% 0.16 155 / 0.1)' : 'oklch(72% 0.13 75 / 0.08)',
          color: live ? 'var(--color-nx-live)' : 'var(--color-nx-stub)',
        }}
      >
        {live ? 'Live' : 'Soon'}
      </span>
    </div>
  );
}

/* ── Logs feed ───────────────────────────────────────────── */

function LogsFeed({ logs, loading }: { logs: LogEntry[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="stagger" style={{ display: 'flex', flexDirection: 'column' }}>
        {[0,1,2,3,4].map(i => <SkeletonRow key={i} />)}
      </div>
    );
  }

  if (logs.length === 0) {
    return (
      <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--color-nx-dim)', fontSize: 13 }}>
        No agent activity yet. Send a chat message to see logs.
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--color-nx-surface)',
        border: '1px solid var(--color-nx-border)',
        borderRadius: 10,
        overflow: 'hidden',
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '80px 1fr 70px 80px',
          gap: 0,
          padding: '10px 16px',
          borderBottom: '1px solid var(--color-nx-border)',
          fontSize: 10,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: 'var(--color-nx-dim)',
          fontWeight: 600,
        }}
      >
        <span>Agent</span>
        <span>Action</span>
        <span style={{ textAlign: 'right' }}>ms</span>
        <span style={{ textAlign: 'right' }}>Time</span>
      </div>

      {/* Log rows */}
      <div className="stagger" style={{ maxHeight: 440, overflowY: 'auto' }}>
        {logs.map((l, i) => (
          <LogRow key={l.id} log={l} even={i % 2 === 0} />
        ))}
      </div>
    </div>
  );
}

function LogRow({ log: l, even }: { log: LogEntry; even: boolean }) {
  const hasError = !!l.error;
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '80px 1fr 70px 80px',
        gap: 0,
        padding: '9px 16px',
        borderBottom: '1px solid var(--color-nx-border-dim)',
        background: even ? 'transparent' : 'oklch(13% 0.015 240 / 0.4)',
        fontSize: 12,
        fontFamily: 'var(--font-mono)',
        color: hasError ? 'var(--color-nx-error)' : 'var(--color-nx-muted)',
      }}
    >
      <span style={{ color: 'var(--color-nx-blue-dim)', fontWeight: 600 }}>{l.agent_name}</span>
      <span style={{ color: hasError ? 'var(--color-nx-error)' : 'var(--color-nx-text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
        {l.error ? `error: ${l.error}` : l.action}
      </span>
      <span style={{ textAlign: 'right', color: 'var(--color-nx-muted)' }}>
        {l.duration_ms != null ? l.duration_ms.toLocaleString() : '—'}
      </span>
      <span style={{ textAlign: 'right', color: 'var(--color-nx-dim)' }}>
        {formatTime(l.created_at)}
      </span>
    </div>
  );
}

function formatTime(iso: string) {
  try {
    return new Date(iso).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return '—';
  }
}

/* ── Skeletons ───────────────────────────────────────────── */

function SkeletonNum() {
  return (
    <div style={{ width: 60, height: 28, borderRadius: 6, background: 'var(--color-nx-raised)', animation: 'pulse-dot 1.5s ease-in-out infinite' }} />
  );
}

function SkeletonCard() {
  return (
    <div style={{ height: 60, background: 'var(--color-nx-surface)', border: '1px solid var(--color-nx-border)', borderRadius: 10, animation: 'pulse-dot 1.5s ease-in-out infinite' }} />
  );
}

function SkeletonRow() {
  return (
    <div style={{ height: 34, margin: '1px 0', background: 'var(--color-nx-surface)', animation: 'pulse-dot 1.5s ease-in-out infinite' }} />
  );
}
