# NEXUS — Sporting Lagos FC AI OS

> AI-powered operating system for **Sporting Lagos FC** ⚽

## Overview

Four AI agents — **Fan, Media, Scout, Ops** — share memory and are
orchestrated via LangGraph. The MVP delivers a fully working Fan Agent
(SONA) on web and WhatsApp, with stub endpoints for the other three.

## Tech Stack

- **Backend**: FastAPI · LangChain + LangGraph · Groq (Llama 3.3 70B)
- **Frontend**: Next.js (TypeScript) · Vanilla CSS
- **Database**: Supabase (Postgres + pgvector)
- **Deployment**: Railway (backend) + Cloudflare Pages (frontend)

## Quick Start

```bash
# Backend
cd backend
cp ../.env.example ../.env   # fill in your keys
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
nexus/
├── backend/app/       # FastAPI + agents + RAG
├── frontend/src/      # Next.js chat UI + admin
├── infra/             # Railway config + Supabase migrations
└── docs/              # Demo script + documentation
```

## Club Identity

- **Full name**: Sporting Lagos Football Club
- **Owner**: Shola Akinlade (co-founder of Paystack)
- **Stadium**: Mobolaji Johnson Arena, Lagos
- **Colors**: Neon Blue `#00BFFF` · Pantone Blue `#003087` · Yellow `#FFD700`

---

Built with 💙 for The Noisy Lagosians.
