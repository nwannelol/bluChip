'use client';

import { useRef, useState, type KeyboardEvent, type FormEvent } from 'react';
import { ArrowUp } from '@phosphor-icons/react';
import type { Agent } from './ChatInterface';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
  agent: Agent;
}

const placeholder: Record<Agent, string> = {
  fan:   'Ask SONA about Sporting Lagos...',
  scout: 'Ask Scout about any player...',
  media: 'Media agent coming soon',
  ops:   'Ops agent coming soon',
};

export default function ChatInput({ onSend, disabled, agent }: Props) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const isStub = agent === 'media' || agent === 'ops';
  const canSend = value.trim().length > 0 && !disabled && !isStub;

  function autoResize() {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 180) + 'px';
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  function submit() {
    if (!canSend) return;
    onSend(value.trim());
    setValue('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    submit();
  }

  return (
    <div
      style={{
        padding: '16px 28px 24px',
        borderTop: '1px solid var(--color-nx-border)',
        background: 'var(--color-nx-base)',
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          display: 'flex',
          gap: 10,
          alignItems: 'flex-end',
          background: 'var(--color-nx-surface)',
          border: '1px solid var(--color-nx-border)',
          borderRadius: 14,
          padding: '12px 12px 12px 16px',
          transition: `border-color 180ms var(--ease-out)`,
        }}
        onFocus={e => (e.currentTarget.style.borderColor = 'var(--color-nx-blue-dim)')}
        onBlur={e => (e.currentTarget.style.borderColor = 'var(--color-nx-border)')}
      >
        <textarea
          ref={textareaRef}
          rows={1}
          value={value}
          onChange={e => { setValue(e.target.value); autoResize(); }}
          onKeyDown={handleKeyDown}
          disabled={disabled || isStub}
          placeholder={placeholder[agent]}
          style={{
            flex: 1,
            background: 'none',
            border: 'none',
            outline: 'none',
            resize: 'none',
            fontSize: 14,
            lineHeight: 1.6,
            color: 'var(--color-nx-text)',
            fontFamily: 'var(--font-sans)',
            maxHeight: 180,
            overflowY: 'auto',
          }}
        />
        <button
          type="submit"
          disabled={!canSend}
          className="pressable"
          style={{
            width: 34,
            height: 34,
            borderRadius: 8,
            border: 'none',
            background: canSend ? 'var(--color-nx-blue)' : 'var(--color-nx-raised)',
            color: canSend ? 'oklch(9% 0.012 240)' : 'var(--color-nx-dim)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: canSend ? 'pointer' : 'not-allowed',
            flexShrink: 0,
            transition: `background 180ms var(--ease-out), color 180ms var(--ease-out)`,
          }}
          aria-label="Send message"
        >
          {disabled ? (
            <Spinner />
          ) : (
            <ArrowUp size={16} weight="bold" />
          )}
        </button>
      </form>
      <div style={{ marginTop: 8, textAlign: 'center', fontSize: 11, color: 'var(--color-nx-dim)' }}>
        Press Enter to send, Shift+Enter for newline
      </div>
    </div>
  );
}

function Spinner() {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 14 14"
      fill="none"
      style={{ animation: 'spin 700ms linear infinite' }}
    >
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      <circle cx="7" cy="7" r="5.5" stroke="currentColor" strokeWidth="1.5" strokeDasharray="22" strokeDashoffset="8" strokeLinecap="round" />
    </svg>
  );
}
