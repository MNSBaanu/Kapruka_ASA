from pydantic import BaseModel
from typing import Any


class MCPError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int
    method: str
    params: dict[str, Any] | None = None


class MCPResponse(BaseModel):
    jsonrpc: str
    id: int
    result: Any = None
    error: dict[str, Any] | None = None
