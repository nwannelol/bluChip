# CLAUDE.md — Club Intelligence Layer (NEXUS)

> Read this file at the start of every session. Do not deviate from these
> conventions without explicit instruction. Do not rewrite working code
> unless asked.

---

## Project Overview

An agentic AI operating system for **Sporting Lagos FC** — a Nigerian
Premier League club founded in 2022 by Shola Akinlade (co-founder of
Paystack). Four AI agents (Fan, Media, Scout, Ops) share memory and are
orchestrated via LangGraph. The MVP delivers a fully working Fan Agent
on web and WhatsApp, with stub endpoints for the other three agents.

This is a pitch-grade MVP. Code must be clean, modular, and impressive
enough to demo to the club owner.

---

## Club Identity (use everywhere — no fictional clubs)

```
Full name:    Sporting Lagos Football Club
Short name:   Sporting Lagos
Abbreviation: SLFC
Nicknames:    The Noisy Lagosians, The Tech Boys, Blue and Yellow
Founded:      February 3, 2022
Owner:        Shola Akinlade
Chairman:     Godwin Enakhena
Head Coach:   Jeffrey Buter
Captain:      Abdulraheem Suleiman (#8, MF)
Stadium:      Mobolaji Johnson Arena (Onikan Stadium)
Capacity:     10,000
Colors:       Neon Blue + Pantone Blue (home) / Yellow (away)
League:       Nigeria Premier Football League (NPFL)
Rivals:       Remo Stars FC, Ikorodu City FC (Lagos Derby)
Website:      https://sportinglagos.com
```

---

## Tech Stack (locked — do not change without instruction)

| Layer | Tool |
|---|---|
| Backend framework | FastAPI (Python) |
| Agent framework | LangChain + LangGraph |
| LLM provider | Groq (`llama-3.3-70b-versatile`) — abstracted via `services/llm.py` |
| Embeddings | `all-MiniLM-L6-v2` via `sentence-transformers` |
| Database | Supabase (Postgres + pgvector) |
| Background jobs | Celery + Upstash Redis |
| Web frontend | Next.js (TypeScript) |
| Deployment | Railway (backend) + Cloudflare Pages (frontend) |
| WhatsApp | Twilio Sandbox |
| Auth (Phase 2) | Supabase Auth |

---

## Project Structure

```
cil/
├── backend/
│   └── app/
│       ├── main.py
│       ├── config.py
│       ├── dependencies.py
│       ├── api/routes/        # chat, whatsapp, media, scout, ops, admin, health
│       ├── agents/            # fan/, media/, scout/, ops/, base.py
│       ├── graph/             # orchestrator.py, state.py, nodes.py
│       ├── rag/               # embeddings.py, retriever.py, ingest.py
│       ├── services/          # llm.py, supabase.py, twilio_svc.py
│       ├── models/            # schemas.py, database.py
│       ├── tasks/             # celery_app.py
│       └── seed/              # club_data.json, seed_db.py
├── frontend/
│   └── src/
│       ├── app/               # chat/, admin/ pages
│       └── components/        # ChatWindow, MessageBubble, ChatInput, etc.
├── infra/
│   ├── railway.toml
│   └── supabase/migrations/
├── docs/
│   └── demo-script.md
├── CLAUDE.md
└── README.md
```

---

## Coding Rules

### General
- Every secret goes in `.env` — nothing hardcoded ever
- Use `pydantic-settings` for all config via `config.py`
- All functions must have type hints
- Keep files under 200 lines — split if longer
- Write one thing per file, one file per task

### Python / Backend
- Python 3.11+
- Use `async`/`await` throughout FastAPI routes
- All database calls go through `services/supabase.py`
- All LLM calls go through `services/llm.py` — never import Groq/OpenAI directly in agent files
- Agents must inherit from `base.py` BaseAgent ABC
- Log every agent action to the `agent_logs` Supabase table

### Frontend
- TypeScript strict mode — no `any` types
- All API calls go through `lib/api.ts` — never fetch directly in components
- Club colors: `#00BFFF` (neon blue), `#003087` (Pantone blue), `#FFD700` (yellow)
- Dark theme only — background `#0a0a0a`, surface `#111111`

### Agents
- Each agent lives in its own folder under `agents/`
- Stub agents must return `"is_stub": true` in every response
- Fan Agent is the only fully implemented agent in Phase 1
- All agents share the `NEXUSState` TypedDict from `graph/state.py`

---

## LangGraph State Shape

```python
class NEXUSState(TypedDict):
    message: str
    channel: str                 # "web" | "whatsapp"
    session_id: str
    target_agent: str            # "fan" | "media" | "scout" | "ops"
    conversation_history: list
    retrieved_docs: list         # RAG results for Fan Agent
    agent_response: str
    sources: list
    error: Optional[str]
```

---

## Fan Agent System Prompt

```
You are SONA, the official AI assistant for Sporting Lagos FC —
nicknamed "The Tech Boys" and "The Noisy Lagosians". You were built
to serve the club's fans with pride and energy.

You know everything about Sporting Lagos:
- Founded February 3, 2022 by Shola Akinlade (co-founder of Paystack)
- Play at Mobolaji Johnson Arena (Onikan Stadium), Lagos
- Colors: Neon Blue and Pantone Blue (home), Yellow (away)
- Captain: Abdulraheem Suleiman (#8)
- Head Coach: Jeffrey Buter
- Big rivals: Remo Stars FC and Ikorodu City FC
- Academy won the Gothia Cup U17 in Sweden (2024)
- Ebenezer Harcourt became Nigeria's youngest senior international (2025)

Personality: passionate, Lagos-proud, warm, knowledgeable.
Speak like a true Sporting Lagos fan. Use "we" and "our" when referring
to the club. Keep answers concise and energetic. If you don't know
something, say so honestly rather than making it up.

Always use context retrieved from the knowledge base before answering.
```

---

## Environment Variables Required

```bash
# LLM
GROQ_API_KEY=
LLM_PROVIDER=groq
LLM_MODEL=llama-3.3-70b-versatile

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886

# Firecrawl
FIRECRAWL_URL=http://localhost:3002
FIRECRAWL_KEY=bluchip-fc-internal

# Redis
UPSTASH_REDIS_URL=

# App
APP_ENV=development
APP_SECRET_KEY=
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_CLUB_NAME=Sporting Lagos FC
NEXT_PUBLIC_CLUB_SHORT=SLFC
NEXT_PUBLIC_PRIMARY_COLOR=#00BFFF
```

---

## Task Build Order (follow strictly)

```
1  → Project scaffolding
2  → Supabase schema (run 001_initial_schema.sql)
3  → Config + services layer
4  → RAG pipeline
5  → Seed data (Sporting Lagos data — not fictional)
6  → Base Agent + Fan Agent
7  → LangGraph orchestrator
8  → Chat API + WhatsApp webhook
9  → Stub agents + endpoints
10 → Admin endpoints
11 → Next.js Chat UI
12 → Next.js Admin Dashboard
13 → Deploy (Railway + Cloudflare)
14 → Demo prep + README
```

Do not start a task until the previous one is confirmed working.

---

## Token Efficiency Rules

- Work on ONE file per session unless explicitly told otherwise
- Read only the files directly relevant to the current task
- Run `/compact` every 30 messages
- Use `/clear` when switching between backend and frontend work
- Never refactor working code unless asked
- Reference existing patterns instead of redescribing them
  (e.g. "use the same structure as `fan/agent.py`")

---

## Demo Constraints

- Total infrastructure cost for MVP: ₦0 (all free tiers)
- Must run from a public URL on demo day
- WhatsApp demo requires Twilio sandbox opt-in code sent in advance
- Admin dashboard must show all 4 agent cards (Fan: Active, others: Stub)
- No auth required for Phase 1 — do not add login screens

---

## What NOT to do

- Do not use fictional club names (Kwara City FC, etc.)
- Do not hardcode API keys
- Do not import LLM providers directly in agent files
- Do not add features outside the current task scope
- Do not start coding without confirming the plan first
- Do not add auth, tests, or CI/CD unless on the relevant task number
