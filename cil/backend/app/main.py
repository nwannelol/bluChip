"""FastAPI application factory for the Club Intelligence Layer."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.api.routes import health


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    settings = Settings()

    # --- Logging ---
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    logger = logging.getLogger("cil")

    # --- Lifespan ---
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        logger.info("⚽ CIL starting up — Sporting Lagos FC")
        yield
        logger.info("CIL shutting down")

    # --- App ---
    app = FastAPI(
        title="CIL — Club Intelligence Layer",
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

    return app


app = create_app()
