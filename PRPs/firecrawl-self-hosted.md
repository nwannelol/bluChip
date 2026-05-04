PRPs/firecrawl-self-hosted.md
COPY
## FEATURE:

Convert the bluChip / NEXUS stack from cloud Firecrawl (api.firecrawl.dev)
to a fully self-hosted Firecrawl instance running as a Docker service
alongside the existing API and Redis containers.

The current setup uses the Firecrawl cloud API. We want to eliminate the
cloud dependency so all scraping happens within our own infrastructure
with no per-request billing and no data leaving our stack.

What needs to change:
- Add a self-hosted Firecrawl service to nexus/infra/docker-compose.yml
  using pre-built images from GitHub Container Registry (do NOT build
  from source — use ghcr.io images so startup is fast)
- Add a Playwright sidecar service so JS-heavy pages (NPFL site) render
  correctly
- Update nexus/backend/.env to replace FIRECRAWL_API_KEY with
  FIRECRAWL_URL and FIRECRAWL_KEY pointing at the local container
- Update whatever service or config file currently references
  api.firecrawl.dev so it points to http://firecrawl:3002 instead
- The API container must depend_on firecrawl so startup order is correct
- Verify the full stack starts cleanly with one command:
    docker compose -f infra/docker-compose.yml up -d


## EXAMPLES:

Read nexus/infra/docker-compose.yml before writing anything.
The existing file has two services: api and redis. The Firecrawl service
block must follow the exact same formatting and comment style already used
in that file. Do not change the api or redis service definitions — only
add to them (add firecrawl to the api depends_on list).

Read nexus/backend/.env before touching any environment variables.
Find every line that references firecrawl or FIRECRAWL and update only
those lines. Do not add or remove any other env vars.

Find whatever file currently initialises the Firecrawl client in the
backend (search for "api.firecrawl.dev" or "FirecrawlApp" across the
codebase) and update only the config/env reading logic — do not rewrite
the client wrapper.


## DOCUMENTATION:

Firecrawl self-hosting guide (read this — it has the exact docker-compose
service blocks to use with pre-built GHCR images):
https://github.com/mendableai/firecrawl/blob/main/SELF_HOST.md

Firecrawl environment variables reference:
https://docs.firecrawl.dev/contributing/self-host


## OTHER CONSIDERATIONS:

Stack constraints — do not deviate:
- Project lives at C:\Users\nwann\bluChip\nexus\
- docker-compose.yml is at nexus/infra/docker-compose.yml
- backend .env is at nexus/backend/.env
- Currently running containers are infra-api-1 and infra-redis-1
- Network name is cil-dev — keep this, add firecrawl to the same network
- Python 3.11, FastAPI, pydantic-settings — all config via settings object
- firecrawl-py SDK v4.24.0 is already installed in the API container

Self-hosted Firecrawl needs these env vars in docker-compose.yml
under the firecrawl service (generate real random values for secrets):
  NUM_WORKERS_PER_QUEUE=8
  PORT=3002
  HOST=0.0.0.0
  REDIS_URL=redis://redis:6379
  REDIS_RATE_LIMIT_URL=redis://redis:6379
  PLAYWRIGHT_MICROSERVICE_URL=http://playwright-service:3000
  TEST_API_KEY=bluchip-fc-internal   ← this is the internal API key

In nexus/backend/.env replace any existing FIRECRAWL line(s) with:
  FIRECRAWL_URL=http://firecrawl:3002
  FIRECRAWL_KEY=bluchip-fc-internal

FIRECRAWL_KEY must exactly match TEST_API_KEY in the firecrawl service.

Do not commit .env — confirm .gitignore already covers it, add if missing.

Success criteria — verify all of these before finishing:
1. docker compose -f infra/docker-compose.yml up -d starts all services
   with no errors (api, redis, firecrawl, playwright-service)
2. docker compose ps shows all four containers as Up
3. This curl returns a markdown field with real page content:
   curl -X POST http://localhost:3002/v1/scrape \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer bluchip-fc-internal" \
     -d '{"url":"https://npfl.com.ng","formats":["markdown"]}'
4. The backend can reach firecrawl — run inside the api container:
   docker exec infra-api-1 python -c \
     "from app.services.firecrawl import scrape; print(scrape('https://npfl.com.ng')[:200])"
5. No hardcoded URLs or keys anywhere in the codebase
