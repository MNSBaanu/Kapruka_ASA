import re
from datetime import datetime, timedelta, timezone
from typing import Any
from app.mcp.tools import call_tool

COLOMBO_TZ = timezone(timedelta(hours=5, minutes=30))
IMAGE_CDN = "https://static2.kapruka.com/product-image/width=330,quality=93,f=auto/"
known_categories: list[str] = []


def colombo_now() -> datetime:
    return datetime.now(COLOMBO_TZ)


def card_image(url: str | None) -> str | None:
    if url and url.startswith("https://www.kapruka.com/"):
        return IMAGE_CDN + url.removeprefix("https://www.kapruka.com/")
    return url


def _amount(value: Any) -> float | None:
    if isinstance(value, dict):
        return value.get("amount")
    return value


def normalize_product(p: dict) -> dict:
    """Shape an MCP product (search result or full product) into what product cards render."""
    price = p.get("price") if isinstance(p.get("price"), dict) else {}
    images = p.get("images") or ([p["image_url"]] if p.get("image_url") else [])
    category = p.get("category")
    item = {
        "id": p.get("id"),
        "name": p.get("name"),
        "price": _amount(p.get("price")),
        "currency": price.get("currency", "LKR"),
        "compare_at_price": _amount(p.get("compare_at_price")),
        "in_stock": p.get("in_stock", True),
        "stock_level": p.get("stock_level"),
        "image": card_image(images[0]) if images else None,
        "url": p.get("url"),
        "category": category.get("name") if isinstance(category, dict) else category,
    }
    if len(images) > 1:
        item["images"] = [card_image(u) for u in images[:5]]
    if len(p.get("variants") or []) > 1:
        item["variants"] = [
            {"name": v.get("name"), "price": _amount(v.get("price")), "in_stock": v.get("in_stock", True)}
            for v in p["variants"][:8]
        ]
    if isinstance(p.get("delivery"), dict) and "island_wide" in p["delivery"]:
        item["island_wide"] = p["delivery"]["island_wide"]
    return item


def compact_for_model(name: str, result: Any) -> dict:
    """Trim MCP payloads to what the model needs, keeping token use low."""
    if not isinstance(result, dict) or "error" in result:
        return result if isinstance(result, dict) else {"result": result}
    if name == "search_products":
        out = {
            "results": [
                {
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "price": _amount(r.get("price")),
                    "currency": (r.get("price") or {}).get("currency", "LKR") if isinstance(r.get("price"), dict) else "LKR",
                    "in_stock": r.get("in_stock"),
                    "stock_level": r.get("stock_level"),
                    "on_sale_from": _amount(r.get("compare_at_price")),
                    "about": (r.get("summary") or "")[:120],
                }
                for r in result.get("results", [])
            ]
        }
        if result.get("next_cursor"):
            out["next_cursor"] = result["next_cursor"]
        if result.get("message"):
            out["message"] = result["message"]
        return out
    if name == "get_product":
        item = normalize_product(result)
        item.pop("image", None)
        item.pop("images", None)
        item["description"] = (result.get("description") or "")[:400]
        item["delivery"] = result.get("delivery")
        return item
    return result


def _pad_city(city: str) -> str:
    return re.sub(r"\b(\d)\b", r"0\1", city)


async def resolve_city(city: str) -> tuple[str | None, list[str]]:
    """Map a user-typed city or alias to Kapruka's canonical delivery city name."""
    city = (city or "").strip()
    if len(city) < 2:
        return None, []
    suggestions: list[str] = []
    for query in dict.fromkeys([city, _pad_city(city)]):
        result = await call_tool("list_delivery_cities", {"query": query, "limit": 10})
        cities = result.get("cities", []) if isinstance(result, dict) else []
        for c in cities:
            if c.get("name", "").lower() == query.lower() or query.lower() in [a.lower() for a in c.get("aliases", [])]:
                return c["name"], []
        if len(cities) == 1:
            return cities[0]["name"], []
        suggestions += [c["name"] for c in cities if c.get("name") not in suggestions]
    return None, suggestions[:8]


async def warm_up() -> None:
    result = await call_tool("list_categories")
    if isinstance(result, dict):
        known_categories[:] = [c["name"] for c in result.get("categories", []) if c.get("name")]
    await call_tool("list_delivery_cities", {"limit": 50})
