"""FastAPI application factory for NEXUS — Sporting Lagos FC AI OS."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.api.routes import analytics, admin, chat, health, whatsapp
from app.seed.refresh_matches import refresh_matches


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = Settings()

    # --- Logging ---
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("nexus")

    # --- Lifespan ---
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("⚽ NEXUS starting up — Sporting Lagos FC")

        # Seed live matches on boot, then refresh hourly
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            refresh_matches,
            "interval",
            hours=1,
            args=[settings],
            id="matches_refresh",
            replace_existing=True,
        )
        scheduler.start()
        logger.info("Matches refresh scheduler started (interval: 1h)")

        # Run once immediately so the knowledge base is fresh on first boot
        import asyncio
        asyncio.create_task(refresh_matches(settings))

        yield

        scheduler.shutdown(wait=False)
        logger.info("NEXUS shutting down")

    # --- App ---
    app = FastAPI(
        title="NEXUS — Sporting Lagos FC AI OS",
        description="AI operating system for Sporting Lagos FC",
        version="0.1.0",
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Routers ---
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(chat.router, prefix="/api/v1", tags=["chat"])
    app.include_router(whatsapp.router, prefix="/api/v1", tags=["whatsapp"])
    app.include_router(admin.router, prefix="/api/v1", tags=["admin"])
    app.include_router(analytics.router, prefix="/api/v1", tags=["analytics"])

    return app


app = create_app()
