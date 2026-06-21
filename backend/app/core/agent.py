from collections.abc import AsyncGenerator
from app.config import settings
from app.core.state import session_store, Session
from app.core.cache import mcp_cache
from app.prompts.system import SYSTEM_PROMPT
from app.mcp import tools as mcp_tools
from google.genai import Client
from google.genai import types
import json

client = Client(api_key=settings.gemini_api_key)

CACHEABLE_TOOLS = {"search_products", "get_product", "list_categories", "list_delivery_cities"}
MAX_ITERATIONS = 10

TOOLS = [
    types.Tool(function_declarations=[
        types.FunctionDeclaration(
            name="search_products",
            description="Search the Kapruka catalog by keyword with optional category, price range, stock, and sort filters.",
            parameters={
                "type": "object",
                "properties": {
                    "q": {"type": "string", "description": "Search keyword (min 3 characters)"},
                    "category": {"type": "string", "description": "Category name filter"},
                    "min_price": {"type": "number", "description": "Minimum price (inclusive)"},
                    "max_price": {"type": "number", "description": "Maximum price (inclusive)"},
                    "in_stock_only": {"type": "boolean", "description": "Only show in-stock items"},
                    "sort": {"type": "string", "description": "Sort order: relevance, price_asc, price_desc, newest, bestseller"},
                    "limit": {"type": "integer", "description": "Number of results (max 50)"},
                    "cursor": {"type": "string", "description": "Pagination cursor from previous response"},
                    "currency": {"type": "string", "description": "Currency code (LKR, USD, GBP, AUD, CAD, EUR)"},
                    "include_stubs": {"type": "boolean", "description": "Include category landing pages in results"},
                },
                "required": ["q"],
            },
        ),
        types.FunctionDeclaration(
            name="get_product",
            description="Get full product details by product ID.",
            parameters={
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Kapruka product ID (e.g. cake00ka002034)"},
                    "currency": {"type": "string", "description": "Currency code (LKR, USD, GBP, AUD, CAD, EUR)"},
                    "type": {"type": "string", "description": "Product type hint (e.g. specialgifts)"},
                },
                "required": ["product_id"],
            },
        ),
        types.FunctionDeclaration(
            name="list_categories",
            description="List top-level categories available on Kapruka.",
            parameters={
                "type": "object",
                "properties": {
                    "depth": {"type": "integer", "description": "Category depth (1 = top level only)"},
                },
            },
        ),
        types.FunctionDeclaration(
            name="list_delivery_cities",
            description="List or search Sri Lankan cities Kapruka delivers to.",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Filter cities by partial match against name or aliases"},
                    "limit": {"type": "integer", "description": "Max results (max 50)"},
                },
            },
        ),
        types.FunctionDeclaration(
            name="check_delivery",
            description="Check delivery date, rate, and perishable warnings to a city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Canonical city name (e.g. Colombo 03, Galle)"},
                    "delivery_date": {"type": "string", "description": "Desired delivery date YYYY-MM-DD (defaults to today)"},
                    "product_id": {"type": "string", "description": "Optional product ID for perishable freshness check"},
                },
                "required": ["city"],
            },
        ),
        types.FunctionDeclaration(
            name="create_order",
            description="Create a guest-checkout order. IMPORTANT: Only call this after the user has confirmed the full order summary with all details.",
            parameters={
                "type": "object",
                "properties": {
                    "cart": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "string", "description": "Kapruka product ID"},
                                "quantity": {"type": "integer", "description": "Quantity (default 1)"},
                                "icing_text": {"type": "string", "description": "Cake icing text (max 120 chars, only for cakes)"},
                            },
                            "required": ["product_id"],
                        },
                        "description": "List of items in cart (1-30 items)",
                    },
                    "recipient": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Recipient name"},
                            "phone": {"type": "string", "description": "Recipient phone (e.g. 0771234567)"},
                        },
                        "required": ["name", "phone"],
                        "description": "Recipient details",
                    },
                    "delivery": {
                        "type": "object",
                        "properties": {
                            "address": {"type": "string", "description": "Street address"},
                            "city": {"type": "string", "description": "Delivery city (must be a Kapruka delivery city)"},
                            "date": {"type": "string", "description": "Delivery date YYYY-MM-DD"},
                            "location_type": {"type": "string", "description": "house, apartment, office, or other"},
                            "instructions": {"type": "string", "description": "Delivery instructions (optional, max 250 chars)"},
                        },
                        "required": ["address", "city", "date"],
                        "description": "Delivery details",
                    },
                    "sender": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Sender name on gift card"},
                            "anonymous": {"type": "boolean", "description": "Show 'Anonymous' on gift card if true"},
                        },
                        "required": ["name"],
                        "description": "Sender details",
                    },
                    "gift_message": {"type": "string", "description": "Gift card message (optional, max 300 chars)"},
                    "currency": {"type": "string", "description": "Currency code (LKR, USD, GBP, AUD, CAD, EUR)"},
                },
                "required": ["cart", "recipient", "delivery", "sender"],
            },
        ),
        types.FunctionDeclaration(
            name="track_order",
            description="Track an existing order by order number.",
            parameters={
                "type": "object",
                "properties": {
                    "order_number": {"type": "string", "description": "Order number from confirmation"},
                },
                "required": ["order_number"],
            },
        ),
    ]),
]


async def _call_mcp_tool(name: str, args: dict) -> str:
    cache_key = f"{name}:{json.dumps(args, sort_keys=True)}"
    if name in CACHEABLE_TOOLS:
        cached = mcp_cache.get(cache_key)
        if cached:
            return json.dumps(cached)

    tool_fn = getattr(mcp_tools, name, None)
    if not tool_fn:
        return json.dumps({"error": f"Unknown tool: {name}"})

    try:
        result = await tool_fn(**args)
        if name in CACHEABLE_TOOLS:
            mcp_cache.set(cache_key, result)
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _build_history(session: Session) -> list[types.Content]:
    history = []
    for msg in session.history:
        role = "user" if msg["role"] == "user" else "model"
        history.append(types.Content(role=role, parts=[types.Part.from_text(msg["content"])]))
    return history


async def chat_stream(session_id: str, message: str) -> AsyncGenerator[dict, None]:
    session = session_store.get_or_create(session_id)
    session.add_message("user", message)

    history = _build_history(session)
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=TOOLS,
    )

    chat = client.chats.create(
        model=settings.gemini_model,
        config=config,
        history=history,
    )

    iteration = 0
    while iteration < MAX_ITERATIONS:
        iteration += 1
        response = chat.send_message(message if iteration == 1 else "")

        if not response.candidates:
            yield {"type": "text", "content": "I didn't get a response. Could you try again?"}
            return

        candidate = response.candidates[0]
        part = candidate.content.parts[0]

        if part.text:
            text = part.text
            session.add_message("assistant", text)
            yield {"type": "text", "content": text}
            return

        if part.function_call:
            fc = part.function_call
            name = fc.name
            args = dict(fc.args) if fc.args else {}
            yield {"type": "tool_call", "tool": name, "args": args}

            result = await _call_mcp_tool(name, args)

            if name == "create_order":
                parsed = json.loads(result) if result.startswith("{") else result
                yield {"type": "order_confirmation", "data": parsed}
                return

            response = chat.send_message(
                types.Part.from_function_response(name=name, response={"result": result}),
            )
            continue

    yield {"type": "text", "content": "Sorry, I'm having trouble processing that. Could you try again?"}
