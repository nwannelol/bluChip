"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {
        "status": "ok",
        "service": "NEXUS — Sporting Lagos FC AI OS",
        "club": "Sporting Lagos FC",
    }
