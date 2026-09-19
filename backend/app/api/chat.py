import json
from collections import defaultdict, deque
from time import monotonic
from fastapi import APIRouter, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.config import settings
from app.core.agent import chat_stream
from app.core.state import session_store

router = APIRouter()
_hits: dict[str, deque] = defaultdict(deque)


class ChatRequest(BaseModel):
    message: str = Field(default="", max_length=2000)
    action: dict | None = None
    profile: dict | None = None


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _rate_limited(key: str) -> bool:
    now = monotonic()
    hits = _hits[key]
    while hits and now - hits[0] > 60:
        hits.popleft()
    if len(hits) >= settings.chat_rate_per_minute:
        return True
    hits.append(now)
    if len(_hits) > 10000:
        for k in [k for k, v in _hits.items() if not v]:
            del _hits[k]
    return False


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post("/chat")
async def chat(body: ChatRequest, request: Request,
               x_session_id: str = Header(alias="X-Session-Id", min_length=8, max_length=64)):
    limited = _rate_limited(_client_key(request))

    async def stream():
        if limited:
            yield _sse({"type": "error", "code": "rate_limited", "message": "Whoa, that's a lot of messages! Give me a few seconds 🙏"})
            yield _sse({"type": "done"})
            return
        if not body.message.strip() and not body.action:
            yield _sse({"type": "done"})
            return
        async for event in chat_stream(x_session_id, body.message, body.action, body.profile):
            yield _sse(event)

    return StreamingResponse(stream(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/reset")
async def reset(x_session_id: str = Header(alias="X-Session-Id", min_length=8, max_length=64)):
    session_store.remove(x_session_id)
    return {"ok": True}
