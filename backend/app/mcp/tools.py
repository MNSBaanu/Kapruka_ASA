import json
from typing import Any
from app.config import settings
from app.core.cache import mcp_cache
from app.mcp.client import mcp_client
from app.mcp.models import MCPError

TOOL_NAMES = {
    "search_products": "kapruka_search_products",
    "get_product": "kapruka_get_product",
    "list_categories": "kapruka_list_categories",
    "list_delivery_cities": "kapruka_list_delivery_cities",
    "check_delivery": "kapruka_check_delivery",
    "create_order": "kapruka_create_order",
    "track_order": "kapruka_track_order",
}

CACHE_TTL = {
    "search_products": settings.cache_ttl_seconds,
    "get_product": settings.cache_ttl_seconds,
    "list_categories": settings.cache_ttl_seconds,
    "list_delivery_cities": settings.cache_ttl_seconds,
    "check_delivery": settings.delivery_cache_ttl_seconds,
}


def _cacheable(name: str, result: Any) -> bool:
    if name not in CACHE_TTL or not isinstance(result, dict) or "error" in result or "text" in result:
        return False
    if name == "search_products":
        return bool(result.get("results"))
    return True


async def call_tool(name: str, args: dict | None = None, use_cache: bool = True) -> Any:
    """Call a Kapruka MCP tool by short name. Returns parsed JSON or {"error", "message"}."""
    if name not in TOOL_NAMES:
        return {"error": "unknown_tool", "message": f"Unknown tool: {name}"}
    params = {k: v for k, v in (args or {}).items() if v is not None}
    params["response_format"] = "json"
    cache_key = f"{name}:{json.dumps(params, sort_keys=True)}"

    if use_cache and name in CACHE_TTL:
        cached = mcp_cache.get(cache_key)
        if cached is not None:
            return cached

    try:
        result = await mcp_client.call_tool(TOOL_NAMES[name], params)
    except MCPError as e:
        return {"error": str(e.code), "message": e.message}
    except Exception as e:
        return {"error": "unavailable", "message": f"Kapruka could not be reached ({type(e).__name__})."}

    if name == "search_products" and isinstance(result, dict) and "text" in result:
        result = {"results": [], "message": result["text"]}
    if _cacheable(name, result):
        mcp_cache.set(cache_key, result, CACHE_TTL[name])
    return result
