# NEXUS — Sporting Lagos FC AI OS

> AI-powered operating system for **Sporting Lagos FC** ⚽

Four AI agents — **Fan, Media, Scout, Ops** — share memory and are
orchestrated via LangGraph. The MVP delivers a fully working Fan Agent
(SONA) on web and WhatsApp, with stub endpoints for the other three.

---

## Tech Stack

- **Backend**: FastAPI · LangChain + LangGraph · Groq (Llama 3.3 70B)
- **Frontend**: Next.js (TypeScript)
- **Database**: Supabase (Postgres + pgvector)
- **Scraping**: Firecrawl (cloud API)
- **Deployment**: Railway (backend) + Cloudflare Pages (frontend)

---

## Quick Start (Docker — recommended)

```bash
# 1. Start all services (API on :8000, Redis on :6379)
docker compose -f nexus/infra/docker-compose.yml up -d

# 2. Stop all services
docker compose -f nexus/infra/docker-compose.yml down

# 3. Rebuild the API container after code changes
docker compose -f nexus/infra/docker-compose.yml up -d --build api

# 4. View API logs (live)
docker compose -f nexus/infra/docker-compose.yml logs -f api

# 5. Open a shell inside the API container
docker exec -it infra-api-1 bash
```

---

## Seed / Knowledge Base

Run these from the project root. Both scripts are idempotent — safe to re-run.

```bash
# Seed static club data (15 hand-crafted Sporting Lagos documents)
docker exec infra-api-1 python -m app.seed.seed_db

# Scrape live web data via Firecrawl and ingest into the knowledge base
# Sources: sportinglagos.com · Wikipedia · NPFL · CNN (Shola article)
# Searches: NPFL results · Jeffrey Buter · Abdulraheem Suleiman · transfers
docker exec infra-api-1 python -m app.seed.ingest_web
```

---

## API Endpoints

### Health check
```bash
curl http://localhost:8000/api/v1/health
```

### Chat — Fan Agent (SONA)
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Who is the captain of Sporting Lagos?",
    "agent": "fan",
    "session_id": "test-001"
  }'
```

### Chat — Stub agents (media / scout / ops)
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Scout me a striker",
    "agent": "scout",
    "session_id": "test-002"
  }'
```
> Stub agents return `"is_stub": true` in the response.

### WhatsApp webhook (simulate Twilio)
```bash
curl -X POST http://localhost:8000/api/v1/whatsapp/webhook \
  -d "Body=Who+is+SONA&From=whatsapp%3A%2B2348012345678&WaId=2348012345678"
```
> Returns TwiML XML. In production, Twilio POSTs to this URL automatically.

### Interactive API docs
```
http://localhost:8000/docs
```

---

## LangGraph Smoke Tests

Run these inside the container to test the orchestrator directly (bypasses HTTP):

```bash
# Test Fan Agent end-to-end
docker exec infra-api-1 python -c "
import asyncio
from app.config import Settings
from app.graph.orchestrator import build_graph

async def main():
    g = build_graph(Settings())
    result = await g.ainvoke({
        'message': 'Who owns Sporting Lagos?',
        'channel': 'web',
        'session_id': 'smoke-001',
        'target_agent': 'fan',
        'conversation_history': [],
        'retrieved_docs': [],
        'agent_response': '',
        'sources': [],
        'error': None,
    })
    print(result['agent_response'])

asyncio.run(main())
"

# Test Scout stub
docker exec infra-api-1 python -c "
import asyncio
from app.config import Settings
from app.graph.orchestrator import build_graph

async def main():
    g = build_graph(Settings())
    result = await g.ainvoke({
        'message': 'Analyze this player',
        'channel': 'web',
        'session_id': 'smoke-002',
        'target_agent': 'scout',
        'conversation_history': [],
        'retrieved_docs': [],
        'agent_response': '',
        'sources': [],
        'error': None,
    })
    print(result['agent_response'])

asyncio.run(main())
"
```

---

## Local Dev (without Docker)

```bash
cd nexus/backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the API server (hot reload)
uvicorn app.main:app --reload --port 8000

# Run seed scripts locally
python -m app.seed.seed_db
python -m app.seed.ingest_web
```

> Note: local runs read `.env` from `nexus/backend/.env`.

---

## Project Structure

```
nexus/
├── backend/
│   └── app/
│       ├── main.py                  # FastAPI app factory
│       ├── config.py                # pydantic-settings config
│       ├── dependencies.py          # get_settings(), get_graph()
│       ├── api/routes/              # health, chat, whatsapp
│       ├── agents/                  # fan/ (live), media/ scout/ ops/ (stubs)
│       ├── graph/                   # orchestrator.py, nodes.py, state.py
│       ├── rag/                     # embeddings.py, retriever.py, ingest.py
│       ├── services/                # llm.py, supabase.py, firecrawl.py, twilio_svc.py
│       ├── models/                  # schemas.py
│       └── seed/                    # club_data.json, seed_db.py, ingest_web.py
├── frontend/                        # Next.js (Task 11)
├── infra/
│   ├── docker-compose.yml
│   ├── railway.toml
│   └── supabase/migrations/         # 001_initial_schema.sql
└── docs/
    └── demo-script.md
```

---

## Club Identity

| | |
|---|---|
| Full name | Sporting Lagos Football Club |
| Owner | Shola Akinlade (co-founder of Paystack) |
| Head Coach | Jeffrey Buter |
| Captain | Abdulraheem Suleiman (#8, MF) |
| Stadium | Mobolaji Johnson Arena (Onikan), Lagos |
| Colors | Neon Blue `#00BFFF` · Pantone Blue `#003087` · Yellow `#FFD700` |
| League | Nigeria Premier Football League (NPFL) |
| Rivals | Remo Stars FC · Ikorodu City FC |

---

Built with 💙 for The Noisy Lagosians.
