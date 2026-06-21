from fastapi import APIRouter, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.core.agent import chat_stream

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(body: ChatRequest, x_session_id: str = Header(default="default", alias="X-Session-Id")):
    async def stream():
        async for event in chat_stream(x_session_id, body.message):
            import json
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
