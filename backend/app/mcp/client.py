from typing import Any
import httpx
from app.mcp.models import MCPRequest, MCPResponse, MCPError
from app.config import settings

_request_id = 0


def _next_id() -> int:
    global _request_id
    _request_id += 1
    return _request_id


def _parse_sse(data: bytes) -> dict | None:
    for block in data.decode().strip().split("\n\n"):
        event_data = None
        for line in block.split("\n"):
            if line.startswith("data:"):
                event_data = line.removeprefix("data:").strip()
        if event_data:
            import json
            return json.loads(event_data)
    return None


def _headers(session_id: str | None = None) -> dict[str, str]:
    h = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        h["Mcp-Session-Id"] = session_id
    return h


class MCPClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.mcp_timeout)
        self._session_id: str | None = None

    async def _send(self, method: str, params: dict | None = None) -> Any:
        body = MCPRequest(id=_next_id(), method=method, params=params)
        resp = await self._client.post(
            settings.mcp_endpoint,
            json=body.model_dump(exclude_none=True),
            headers=_headers(self._session_id),
        )
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid

        content_type = resp.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            parsed = _parse_sse(resp.content)
            if not parsed:
                raise MCPError(-1, "Empty SSE response")
        else:
            parsed = resp.json()

        mcp_resp = MCPResponse(**parsed)
        if mcp_resp.error:
            raise MCPError(
                code=mcp_resp.error.get("code", -1),
                message=mcp_resp.error.get("message", "Unknown error"),
            )
        return mcp_resp.result

    async def initialize(self) -> None:
        await self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "kapruka-asa", "version": "1.0.0"},
        })

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        # FastMCP wraps single-param tools under a "params" key
        return await self._send("tools/call", {
            "name": name,
            "arguments": {"params": arguments or {}},
        })

    async def close(self) -> None:
        await self._client.aclose()


mcp_client = MCPClient()
