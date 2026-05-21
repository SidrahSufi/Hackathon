"""Health endpoint — used by Cloud Run for liveness checks."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    return {"status": "ok", "version": "0.1.0"}
