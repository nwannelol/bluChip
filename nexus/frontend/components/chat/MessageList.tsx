import type { Message } from './ChatInterface';

interface Props {
  messages: Message[];
}

const agentLabel: Record<string, string> = {
  fan:   'SONA',
  scout: 'Scout',
  media: 'Media',
  ops:   'Ops',
};

export default function MessageList({ messages }: Props) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {messages.map(m => (
        <MessageBubble key={m.id} message={m} />
      ))}
    </div>
  );
}

function MessageBubble({ message: m }: { message: Message }) {
  const isUser = m.role === 'user';

  if (isUser) {
    return (
      <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
        <div
          style={{
            maxWidth: '72%',
            background: 'var(--color-nx-raised)',
            border: '1px solid var(--color-nx-border)',
            borderRadius: '16px 16px 4px 16px',
            padding: '12px 16px',
            fontSize: 14,
            lineHeight: 1.6,
            color: 'var(--color-nx-text)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
          }}
        >
          {m.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
      {/* Agent avatar */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: 8,
          background: 'var(--color-nx-blue-wash)',
          border: '1px solid oklch(72% 0.16 215 / 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--color-nx-blue)', letterSpacing: '0.04em' }}>
          {(agentLabel[m.agent ?? 'fan'] ?? 'AI')[0]}
        </span>
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        {/* Agent label */}
        <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--color-nx-blue)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 6 }}>
          {agentLabel[m.agent ?? 'fan'] ?? 'AI'}
        </div>

        {/* Content */}
        <div
          style={{
            fontSize: 14,
            lineHeight: 1.7,
            color: 'var(--color-nx-text)',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxWidth: '80ch',
          }}
        >
          {m.content}
          {m.streaming && <span className="cursor" aria-hidden />}
        </div>
      </div>
    </div>
  );
}
