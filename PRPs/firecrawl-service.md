PRPs/firecrawl-service.md
COPY
## FEATURE:

Integrate self-hosted Firecrawl into the bluChip CIL as a web intelligence
service. Firecrawl gives the Scout Agent and Media Agent the ability to
scrape and search the live web — pulling player profiles, NPFL match data,
transfer news, and post-match coverage as clean markdown that agents can
reason over directly.

Specifically:
- Self-hosted Firecrawl runs as a Railway service alongside the FastAPI backend
- A `services/firecrawl.py` wrapper follows the exact same pattern as
  `services/llm.py` — agents never import firecrawl directly
- `FIRECRAWL_URL` and `FIRECRAWL_KEY` are added to `config.py` via
  pydantic-settings, never hardcoded
- Scout Agent gets a `scrape_player` tool and a `search_transfers` tool
- Media Agent gets a `search_match_coverage` tool
- `infra/railway.toml` is updated to declare the Firecrawl service
- `infra/docker-compose.yml` is created for local dev so the full stack
  (FastAPI + Firecrawl + Redis) starts with one command


## EXAMPLES:

Read `cil/backend/app/services/llm.py` before writing anything.
The firecrawl service wrapper must follow the exact same structure:
- A settings-aware initialisation function (not a global singleton)
- All config read from `settings` (pydantic-settings), never os.getenv directly
- Typed return values, async where the SDK supports it
- File stays under 200 lines

The Scout Agent tools must follow the same pattern as any existing tools
in `cil/backend/app/agents/`. Each tool is a standalone async function
decorated with the LangChain @tool decorator, imported into the agent's
tool list — not inlined in the agent class.


## DOCUMENTATION:

Firecrawl self-hosting guide:
https://docs.firecrawl.dev/contributing/self-host

Firecrawl Python SDK reference:
https://docs.firecrawl.dev/sdks/python

Firecrawl docker-compose source (use pre-built GHCR images, do not build
from source — this avoids a multi-minute build and keeps Railway deploys fast):
https://github.com/firecrawl/firecrawl/blob/main/SELF_HOST.md

Railway service configuration reference:
https://docs.railway.app/reference/config-as-code


## OTHER CONSIDERATIONS:

Stack constraints from sportingMD.md — do not deviate:
- Python 3.11+, FastAPI, async/await throughout
- All config via pydantic-settings in config.py — add these two fields:
    FIRECRAWL_URL: str = "http://localhost:3002"
    FIRECRAWL_KEY: str = "bluchip-fc-internal"
- Add both vars to the .env.example block in sportingMD.md
- The firecrawl service on Railway must be named "firecrawl" so the
  internal Railway URL resolves as http://firecrawl.railway.internal:3002
  and FIRECRAWL_URL can be set to that in the Railway environment

Self-hosted limitations to be aware of:
- /agent and /browser endpoints are NOT available in self-hosted mode
- Use /v1/scrape for single URLs and /v1/search for keyword queries
- Playwright service must be running for JS-heavy pages (NPFL site uses JS)
- Every request comes from one IP — if NPFL.com blocks it, add proxy vars
  HTTP_PROXY and HTTPS_PROXY to the firecrawl service env on Railway

File placement (strict):
- cil/backend/app/services/firecrawl.py   ← service wrapper
- cil/backend/app/agents/scout/tools.py   ← scrape_player, search_transfers
- cil/backend/app/agents/media/tools.py   ← search_match_coverage
- cil/infra/docker-compose.yml            ← local dev only
- cil/infra/railway.toml                  ← update, do not recreate

Do not touch:
- services/llm.py
- services/supabase.py
- Any existing agent files outside scout/ and media/
- The LangGraph state shape in graph/state.py

Success criteria — all must pass before closing this task:
1. `docker compose -f infra/docker-compose.yml up -d` starts cleanly locally
2. curl test returns markdown from http://localhost:3002/v1/scrape
3. `from app.services.firecrawl import scrape, search` imports without error
4. Scout Agent returns scraped content when given an NPFL player URL
5. Media Agent returns post-match article text when given a match search query
6. No API keys or URLs are hardcoded anywhere — all read from settings
