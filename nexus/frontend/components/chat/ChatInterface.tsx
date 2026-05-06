'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { streamChat } from '@/lib/api';
import AgentSelector from './AgentSelector';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export type Agent = 'fan' | 'scout' | 'media' | 'ops';

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  agent?: Agent;
  streaming?: boolean;
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function getSessionId() {
  if (typeof window === 'undefined') return uid();
  const key = 'nx_session';
  let id = localStorage.getItem(key);
  if (!id) { id = uid(); localStorage.setItem(key, id); }
  return id;
}

export default function ChatInterface() {
  const [agent, setAgent] = useState<Agent>('fan');
  const [messages, setMessages] = useState<Message[]>([]);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef(getSessionId());
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = useCallback(async (text: string) => {
    if (!text.trim() || streaming) return;
    setError(null);

    const userMsg: Message = { id: uid(), role: 'user', content: text };
    const assistantId = uid();
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      agent,
      streaming: true,
    };

    setMessages(prev => [...prev, userMsg, assistantMsg]);
    setStreaming(true);

    await streamChat(
      text,
      agent,
      sessionId.current,
      (token) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId ? { ...m, content: m.content + token } : m
          )
        );
      },
      () => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId ? { ...m, streaming: false } : m
          )
        );
        setStreaming(false);
      },
      (err) => {
        setMessages(prev =>
          prev.map(m =>
            m.id === assistantId
              ? { ...m, content: 'Something went wrong. Please try again.', streaming: false }
              : m
          )
        );
        setStreaming(false);
        setError(err.message);
      },
    );
  }, [agent, streaming]);

  return (
    <div className="flex min-h-[100dvh]">
      {/* Sidebar */}
      <aside
        style={{
          width: 260,
          flexShrink: 0,
          background: 'var(--color-nx-surface)',
          borderRight: '1px solid var(--color-nx-border)',
          display: 'flex',
          flexDirection: 'column',
          padding: '28px 20px',
        }}
      >
        {/* Wordmark */}
        <div style={{ marginBottom: 36 }}>
          <div
            style={{
              fontSize: 11,
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              color: 'var(--color-nx-blue)',
              fontWeight: 600,
              marginBottom: 4,
            }}
          >
            Sporting Lagos FC
          </div>
          <div
            style={{
              fontSize: 22,
              fontWeight: 700,
              letterSpacing: '-0.03em',
              color: 'var(--color-nx-text)',
            }}
          >
            NEXUS
          </div>
          <div
            style={{
              fontSize: 12,
              color: 'var(--color-nx-muted)',
              marginTop: 2,
            }}
          >
            AI Operating System
          </div>
        </div>

        {/* Agent selector */}
        <div style={{ fontSize: 10, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-nx-dim)', marginBottom: 12, fontWeight: 600 }}>
          Agents
        </div>
        <AgentSelector selected={agent} onChange={setAgent} />

        {/* Footer */}
        <div style={{ marginTop: 'auto', paddingTop: 24, borderTop: '1px solid var(--color-nx-border)' }}>
          <a
            href="/admin"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: 13,
              color: 'var(--color-nx-muted)',
              textDecoration: 'none',
              transition: `color 200ms var(--ease-out)`,
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--color-nx-text)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--color-nx-muted)')}
          >
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-nx-live)', display: 'inline-block', flexShrink: 0 }} className="pulse" />
            Operations
          </a>
        </div>
      </aside>

      {/* Main */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Header strip */}
        <div
          style={{
            padding: '16px 28px',
            borderBottom: '1px solid var(--color-nx-border)',
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <AgentChip agent={agent} />
        </div>

        {/* Messages */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '24px 28px' }}>
          {messages.length === 0 ? (
            <EmptyState agent={agent} />
          ) : (
            <MessageList messages={messages} />
          )}
          <div ref={bottomRef} />
        </div>

        {/* Error */}
        {error && (
          <div style={{ padding: '8px 28px', background: 'oklch(62% 0.16 15 / 0.1)', borderTop: '1px solid oklch(62% 0.16 15 / 0.3)', fontSize: 13, color: 'var(--color-nx-error)' }}>
            {error}
          </div>
        )}

        {/* Input */}
        <ChatInput onSend={send} disabled={streaming} agent={agent} />
      </div>
    </div>
  );
}

function AgentChip({ agent }: { agent: Agent }) {
  const meta: Record<Agent, { label: string; live: boolean }> = {
    fan:   { label: 'SONA — Fan Assistant', live: true },
    scout: { label: 'Scout — Transfer Intelligence', live: true },
    media: { label: 'Media Agent', live: false },
    ops:   { label: 'Ops Agent', live: false },
  };
  const { label, live } = meta[agent];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          background: live ? 'var(--color-nx-live)' : 'var(--color-nx-stub)',
          display: 'inline-block',
          flexShrink: 0,
        }}
        className={live ? 'pulse' : ''}
      />
      <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--color-nx-text)' }}>{label}</span>
    </div>
  );
}

function EmptyState({ agent }: { agent: Agent }) {
  const prompts: Record<Agent, string[]> = {
    fan: [
      'Who is the captain of Sporting Lagos?',
      'When was the club founded?',
      'What happened at the Gothia Cup?',
    ],
    scout: [
      'Which Nigerian wingers are in form this season?',
      'Could Sadio Mane benefit Sporting Lagos?',
      'Find me a reliable left-back under 25.',
    ],
    media: ['Coming soon'],
    ops:   ['Coming soon'],
  };
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        justifyContent: 'center',
        height: '100%',
        minHeight: 320,
        gap: 24,
      }}
    >
      <div>
        <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: '-0.03em', color: 'var(--color-nx-text)', marginBottom: 6 }}>
          What can I help with?
        </div>
        <div style={{ fontSize: 14, color: 'var(--color-nx-muted)', maxWidth: '52ch' }}>
          {agent === 'fan'
            ? 'Ask SONA anything about Sporting Lagos FC — the club, players, results, or history.'
            : agent === 'scout'
            ? 'Ask the Scout about any player, transfer target, or opposition anywhere in the world.'
            : 'This agent is coming in a future release.'}
        </div>
      </div>
      {agent !== 'media' && agent !== 'ops' && (
        <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {prompts[agent].map((p, i) => (
            <SuggestionPill key={i} text={p} />
          ))}
        </div>
      )}
    </div>
  );
}

function SuggestionPill({ text }: { text: string }) {
  return (
    <button
      style={{
        background: 'var(--color-nx-surface)',
        border: '1px solid var(--color-nx-border)',
        borderRadius: 8,
        padding: '10px 14px',
        fontSize: 13,
        color: 'var(--color-nx-muted)',
        cursor: 'pointer',
        textAlign: 'left',
        transition: `color 180ms var(--ease-out), border-color 180ms var(--ease-out)`,
      }}
      className="pressable"
      onMouseEnter={e => {
        e.currentTarget.style.color = 'var(--color-nx-text)';
        e.currentTarget.style.borderColor = 'var(--color-nx-blue-dim)';
      }}
      onMouseLeave={e => {
        e.currentTarget.style.color = 'var(--color-nx-muted)';
        e.currentTarget.style.borderColor = 'var(--color-nx-border)';
      }}
    >
      {text}
    </button>
  );
}
