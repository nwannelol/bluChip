-- NEXUS — Club Intelligence Layer
-- Migration 001: Initial schema for Sporting Lagos FC
-- Run this in the Supabase SQL editor before starting the backend.

-- ============================================================
-- Extensions
-- ============================================================

create extension if not exists "uuid-ossp";
create extension if not exists "vector";          -- pgvector for RAG embeddings


-- ============================================================
-- knowledge_base
-- Stores chunked documents for RAG retrieval.
-- Embedding dim = 384 (all-MiniLM-L6-v2).
-- ============================================================

create table if not exists knowledge_base (
    id          uuid        primary key default uuid_generate_v4(),
    content     text        not null,
    metadata    jsonb       not null default '{}',   -- {source, category, url, …}
    embedding   vector(384) not null,
    created_at  timestamptz not null default now()
);

-- IVFFlat index for fast approximate nearest-neighbour search.
-- nlist=100 is a safe default for an MVP knowledge base of < 100k rows.
create index if not exists knowledge_base_embedding_idx
    on knowledge_base
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);


-- ============================================================
-- conversations
-- One row per user session (web or WhatsApp).
-- ============================================================

create table if not exists conversations (
    id          uuid        primary key default uuid_generate_v4(),
    session_id  text        not null unique,
    channel     text        not null check (channel in ('web', 'whatsapp')),
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

create index if not exists conversations_session_id_idx on conversations (session_id);


-- ============================================================
-- messages
-- Individual turns within a conversation.
-- ============================================================

create table if not exists messages (
    id              uuid        primary key default uuid_generate_v4(),
    conversation_id uuid        not null references conversations (id) on delete cascade,
    role            text        not null check (role in ('user', 'assistant')),
    content         text        not null,
    agent           text        not null check (agent in ('fan', 'media', 'scout', 'ops')),
    sources         jsonb       not null default '[]',   -- RAG citations returned to user
    created_at      timestamptz not null default now()
);

create index if not exists messages_conversation_id_idx on messages (conversation_id);


-- ============================================================
-- agent_logs
-- Immutable audit trail — every agent action is appended here.
-- Required by CLAUDE.md: "Log every agent action to agent_logs."
-- ============================================================

create table if not exists agent_logs (
    id          uuid        primary key default uuid_generate_v4(),
    agent_name  text        not null check (agent_name in ('fan', 'media', 'scout', 'ops')),
    session_id  text        not null,
    action      text        not null,   -- e.g. "rag_retrieve", "llm_call", "stub_response"
    input       jsonb       not null default '{}',
    output      jsonb       not null default '{}',
    duration_ms integer,
    error       text,
    created_at  timestamptz not null default now()
);

create index if not exists agent_logs_session_id_idx  on agent_logs (session_id);
create index if not exists agent_logs_agent_name_idx  on agent_logs (agent_name);
create index if not exists agent_logs_created_at_idx  on agent_logs (created_at desc);


-- ============================================================
-- Helper function: cosine similarity search for RAG retriever
-- Returns the top `match_count` chunks whose embedding is
-- closest to `query_embedding`, filtered by `match_threshold`.
-- ============================================================

create or replace function match_knowledge_base (
    query_embedding vector(384),
    match_threshold float  default 0.5,
    match_count     int    default 5
)
returns table (
    id          uuid,
    content     text,
    metadata    jsonb,
    similarity  float
)
language sql stable
as $$
    select
        kb.id,
        kb.content,
        kb.metadata,
        1 - (kb.embedding <=> query_embedding) as similarity
    from knowledge_base kb
    where 1 - (kb.embedding <=> query_embedding) >= match_threshold
    order by kb.embedding <=> query_embedding
    limit match_count;
$$;


-- ============================================================
-- Auto-update conversations.updated_at on message insert
-- ============================================================

create or replace function touch_conversation_updated_at()
returns trigger language plpgsql as $$
begin
    update conversations
    set updated_at = now()
    where id = new.conversation_id;
    return new;
end;
$$;

create trigger messages_touch_conversation
    after insert on messages
    for each row execute function touch_conversation_updated_at();
