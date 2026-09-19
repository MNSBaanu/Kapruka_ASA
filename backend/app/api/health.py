from time import monotonic
from fastapi import APIRouter
from app.config import settings
from app.core.agent import client
from app.mcp.client import mcp_client

router = APIRouter()
CHECK_EVERY_SECONDS = 30
_last: dict = {"at": -CHECK_EVERY_SECONDS, "result": None}


async def _gemini_ok() -> bool:
    if not settings.gemini_api_key:
        return False
    try:
        await client.aio.models.get(model=settings.gemini_model)
        return True
    except Exception:
        return False


@router.get("/health")
async def health():
    if monotonic() - _last["at"] >= CHECK_EVERY_SECONDS:
        mcp_ok, gemini_ok = await mcp_client.ping(), await _gemini_ok()
        _last["result"] = {
            "status": "ok" if mcp_ok and gemini_ok else "degraded",
            "mcp": mcp_ok,
            "gemini": gemini_ok,
            "model": settings.gemini_model,
        }
        _last["at"] = monotonic()
    return _last["result"]
