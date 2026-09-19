import asyncio
import itertools
import json
import re
from time import monotonic
from typing import Any
import httpx
from app.mcp.models import MCPRequest, MCPResponse, MCPError
from app.config import settings

PROTOCOL_VERSION = "2025-03-26"
MAX_RATE_WAIT_SECONDS = 10
_ERROR_TEXT = re.compile(r"^Error \(([\w-]+)\):\s*(.*)", re.S)
_ids = itertools.count(1)


def _parse_sse(data: bytes) -> dict | None:
    for block in data.decode().strip().split("\n\n"):
        event_data = None
        for line in block.split("\n"):
            if line.startswith("data:"):
                event_data = line.removeprefix("data:").strip()
        if event_data:
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


def parse_tool_result(result: Any) -> Any:
    """Unwrap an MCP tools/call result ({content:[{type:text,text}], isError}) into data."""
    if not isinstance(result, dict) or "content" not in result:
        return result
    text = "\n".join(
        block.get("text", "") for block in result.get("content") or [] if block.get("type") == "text"
    ).strip()
    if result.get("isError"):
        return {"error": "invalid_request", "message": text[:500]}
    match = _ERROR_TEXT.match(text)
    if match:
        return {"error": match.group(1), "message": match.group(2).strip()}
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return {"text": text}


class MCPClient:
    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=settings.mcp_timeout)
        self._session_id: str | None = None
        self._ready = False
        self._init_lock = asyncio.Lock()
        self.rate_remaining: int | None = None
        self._rate_reset_at = 0.0

    def _track_rate(self, resp: httpx.Response) -> None:
        remaining = resp.headers.get("ratelimit-remaining")
        reset = resp.headers.get("ratelimit-reset")
        if remaining is not None and remaining.isdigit():
            self.rate_remaining = int(remaining)
        if reset is not None and reset.isdigit():
            self._rate_reset_at = monotonic() + int(reset)

    def _rate_wait(self) -> float:
        return max(0.0, min(self._rate_reset_at - monotonic(), MAX_RATE_WAIT_SECONDS))

    async def _post(self, payload: dict) -> httpx.Response:
        if self.rate_remaining == 0:
            await asyncio.sleep(self._rate_wait())
        resp = await self._client.post(settings.mcp_endpoint, json=payload, headers=_headers(self._session_id))
        self._track_rate(resp)
        if resp.status_code == 429:
            await asyncio.sleep(self._rate_wait() or 2)
            resp = await self._client.post(settings.mcp_endpoint, json=payload, headers=_headers(self._session_id))
            self._track_rate(resp)
            if resp.status_code == 429:
                raise MCPError("rate_limited", "Kapruka is getting a lot of requests right now. Try again in a minute.")
        return resp

    async def _send(self, method: str, params: dict | None = None) -> Any:
        body = MCPRequest(id=next(_ids), method=method, params=params)
        resp = await self._post(body.model_dump(exclude_none=True))
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self._session_id = sid
        if resp.status_code == 404 and self._session_id:
            raise MCPError("session_expired", "MCP session expired")
        if resp.status_code >= 400:
            raise MCPError(resp.status_code, resp.text[:200] or "MCP request failed")

        if "text/event-stream" in resp.headers.get("content-type", ""):
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
        async with self._init_lock:
            if self._ready:
                return
            self._session_id = None
            await self._send("initialize", {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "kapruka-asa", "version": "2.0.0"},
            })
            await self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
            self._ready = True

    async def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        if not self._ready:
            await self.initialize()
        payload = {"name": name, "arguments": {"params": arguments or {}}}
        try:
            result = await self._send("tools/call", payload)
        except MCPError as e:
            if e.code != "session_expired":
                raise
            self._ready = False
            await self.initialize()
            result = await self._send("tools/call", payload)
        return parse_tool_result(result)

    async def ping(self) -> bool:
        try:
            if not self._ready:
                await self.initialize()
            await self._send("ping")
            return True
        except MCPError as e:
            if e.code == "session_expired":
                self._ready = False
            return False
        except Exception:
            return False

    async def close(self) -> None:
        await self._client.aclose()


mcp_client = MCPClient()
