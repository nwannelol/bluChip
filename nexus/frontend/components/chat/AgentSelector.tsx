'use client';

import type { Agent } from './ChatInterface';

interface AgentOption {
  id: Agent;
  label: string;
  sublabel: string;
  live: boolean;
}

const AGENTS: AgentOption[] = [
  { id: 'fan',   label: 'SONA',   sublabel: 'Fan assistant',          live: true  },
  { id: 'scout', label: 'Scout',  sublabel: 'Transfer intelligence',  live: true  },
  { id: 'media', label: 'Media',  sublabel: 'Press & coverage',       live: false },
  { id: 'ops',   label: 'Ops',    sublabel: 'Club operations',        live: false },
];

interface Props {
  selected: Agent;
  onChange: (a: Agent) => void;
}

export default function AgentSelector({ selected, onChange }: Props) {
  return (
    <div className="stagger" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      {AGENTS.map(a => (
        <AgentRow
          key={a.id}
          option={a}
          active={selected === a.id}
          onClick={() => a.live && onChange(a.id)}
        />
      ))}
    </div>
  );
}

function AgentRow({
  option,
  active,
  onClick,
}: {
  option: AgentOption;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      disabled={!option.live}
      className="pressable"
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '10px 12px',
        borderRadius: 8,
        border: 'none',
        cursor: option.live ? 'pointer' : 'default',
        background: active ? 'var(--color-nx-blue-wash)' : 'transparent',
        textAlign: 'left',
        width: '100%',
        transition: `background 180ms var(--ease-out)`,
        opacity: option.live ? 1 : 0.45,
      }}
      onMouseEnter={e => {
        if (!active && option.live)
          e.currentTarget.style.background = 'var(--color-nx-raised)';
      }}
      onMouseLeave={e => {
        if (!active)
          e.currentTarget.style.background = 'transparent';
      }}
    >
      {/* Status dot */}
      <span
        style={{
          width: 7,
          height: 7,
          borderRadius: '50%',
          flexShrink: 0,
          background: option.live ? 'var(--color-nx-live)' : 'var(--color-nx-dim)',
        }}
        className={option.live ? 'pulse' : ''}
      />

      {/* Labels */}
      <span style={{ flex: 1, minWidth: 0 }}>
        <span
          style={{
            display: 'block',
            fontSize: 13,
            fontWeight: 500,
            color: active ? 'var(--color-nx-blue)' : 'var(--color-nx-text)',
            letterSpacing: '-0.01em',
          }}
        >
          {option.label}
        </span>
        <span
          style={{
            display: 'block',
            fontSize: 11,
            color: 'var(--color-nx-muted)',
            marginTop: 1,
          }}
        >
          {option.sublabel}
        </span>
      </span>

      {/* Badge */}
      {option.live ? (
        <span
          style={{
            fontSize: 10,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            padding: '2px 6px',
            borderRadius: 4,
            background: active
              ? 'oklch(72% 0.16 215 / 0.2)'
              : 'oklch(70% 0.16 155 / 0.12)',
            color: active ? 'var(--color-nx-blue)' : 'var(--color-nx-live)',
            fontWeight: 600,
          }}
        >
          Live
        </span>
      ) : (
        <span
          style={{
            fontSize: 10,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            padding: '2px 6px',
            borderRadius: 4,
            background: 'oklch(72% 0.13 75 / 0.1)',
            color: 'var(--color-nx-stub)',
            fontWeight: 600,
          }}
        >
          Soon
        </span>
      )}
    </button>
  );
}
