from app.mcp.client import mcp_client
from typing import Any


async def search_products(
    q: str | None = None,
    category: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    in_stock_only: bool | None = None,
    sort: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    currency: str | None = None,
    include_stubs: bool | None = None,
) -> Any:
    params = {k: v for k, v in locals().items() if v is not None}
    return await mcp_client.call_tool("kapruka_search_products", params)


async def get_product(product_id: str, currency: str | None = None, type: str | None = None) -> Any:
    params = {"product_id": product_id}
    if currency:
        params["currency"] = currency
    if type:
        params["type"] = type
    return await mcp_client.call_tool("kapruka_get_product", params)


async def list_categories(depth: int | None = None) -> Any:
    params = {}
    if depth is not None:
        params["depth"] = depth
    return await mcp_client.call_tool("kapruka_list_categories", params)


async def list_delivery_cities(query: str | None = None, limit: int | None = None) -> Any:
    params = {}
    if query is not None:
        params["query"] = query
    if limit is not None:
        params["limit"] = limit
    return await mcp_client.call_tool("kapruka_list_delivery_cities", params)


async def check_delivery(city: str, delivery_date: str | None = None, product_id: str | None = None) -> Any:
    params = {"city": city}
    if delivery_date:
        params["delivery_date"] = delivery_date
    if product_id:
        params["product_id"] = product_id
    return await mcp_client.call_tool("kapruka_check_delivery", params)


async def create_order(
    cart: list[dict],
    recipient: dict,
    delivery: dict,
    sender: dict | None = None,
    gift_message: str | None = None,
    currency: str | None = None,
) -> Any:
    params = {
        "cart": cart,
        "recipient": recipient,
        "delivery": delivery,
    }
    if sender:
        params["sender"] = sender
    if gift_message:
        params["gift_message"] = gift_message
    if currency:
        params["currency"] = currency
    return await mcp_client.call_tool("kapruka_create_order", params)


async def track_order(order_number: str) -> Any:
    return await mcp_client.call_tool("kapruka_track_order", {
        "order_number": order_number,
    })
