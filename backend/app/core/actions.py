import asyncio
import re
from datetime import date, timedelta
from time import time
from typing import Any
from google.genai import types
from app.core.catalog import colombo_now, compact_for_model, normalize_product, resolve_city
from app.core.state import Session
from app.mcp.tools import call_tool

LOCATION_TYPES = {"house", "apartment", "office", "other"}
MAX_ORDERS_PER_HOUR = 3
ORDER_ERROR_HINTS = {
    "empty_cart": "The cart is empty. Help the customer pick something first.",
    "missing_field": "A required detail is missing. Ask the customer for it, then call prepare_order again.",
    "past_delivery_date": "That date has passed in Sri Lanka time. Offer the next available date.",
    "product_not_found": "One product no longer exists. Tell the customer and offer a close alternative (ask first).",
    "product_out_of_stock": "An item just sold out. Tell the customer which one and offer alternatives (ask first).",
    "city_not_deliverable": "Kapruka doesn't deliver to that city. Use list_delivery_cities to find the nearest one.",
    "date_not_deliverable": "That date can't be delivered. Use check_delivery to find the next available date.",
    "city_not_deliverable_for_item": "An item can't reach that city. Name the blocking item; offer to change city or swap that item. Never retry with the same city.",
    "rate_limited": "Kapruka is busy. Apologise and ask them to try again in a minute.",
}

Result = tuple[dict, list[dict]]


def _p(type_: str, description: str, **extra) -> dict:
    return {"type": type_, "description": description, **extra}


DECLARATIONS = [
    types.FunctionDeclaration(
        name="search_products",
        description="Search the live Kapruka catalog (~120k products: gifts, cakes, flowers, groceries, electronics, fashion, home). Works best with specific 2-3 word phrases ('chocolate cake', 'red roses bouquet', 'basmati rice 5kg'); single generic words often return nothing. If nothing matches, the category and then price filters are relaxed automatically. Results are shown to the customer as cards only when you write [[product:ID]] markers.",
        parameters={"type": "object", "properties": {
            "q": _p("string", "Specific search words, min 3 characters (e.g. 'red roses', 'rice 5kg', 'bluetooth earbuds'). Translate Sinhala/Tamil/Singlish needs into English product words."),
            "category": _p("string", "Optional category name from the known category list."),
            "min_price": _p("number", "Minimum price."),
            "max_price": _p("number", "Maximum price (use the customer's budget)."),
            "in_stock_only": _p("boolean", "Defaults to true. Set false only if the customer asks for sold-out items."),
            "sort": _p("string", "relevance (default), price_asc, price_desc, newest, bestseller."),
            "limit": _p("integer", "Number of results, default 6, max 12."),
            "cursor": _p("string", "next_cursor from a previous search to show more (max 3 pages)."),
            "currency": _p("string", "LKR (default), USD, GBP, AUD, CAD or EUR."),
        }, "required": ["q"]},
    ),
    types.FunctionDeclaration(
        name="get_product",
        description="Full details for one product: description, variants, all images, stock, delivery scope.",
        parameters={"type": "object", "properties": {
            "product_id": _p("string", "Product ID from search results."),
            "currency": _p("string", "LKR (default), USD, GBP, AUD, CAD or EUR."),
        }, "required": ["product_id"]},
    ),
    types.FunctionDeclaration(
        name="list_delivery_cities",
        description="Find Kapruka delivery cities by name or local alias.",
        parameters={"type": "object", "properties": {
            "query": _p("string", "Partial city name or alias."),
            "limit": _p("integer", "Max results (default 10)."),
        }},
    ),
    types.FunctionDeclaration(
        name="check_delivery",
        description="Check if delivery to a city on a date is possible, the flat delivery fee, and perishable warnings. City aliases are resolved automatically. If the date is not available, the next available date is returned.",
        parameters={"type": "object", "properties": {
            "city": _p("string", "City name or alias (e.g. 'Colombo 3', 'Kandy', 'Galle')."),
            "delivery_date": _p("string", "YYYY-MM-DD, Sri Lanka time. Omit for today."),
            "product_id": _p("string", "Product to check against (always pass for cakes, flowers, food, combos)."),
        }, "required": ["city"]},
    ),
    types.FunctionDeclaration(
        name="track_order",
        description="Track a paid Kapruka order by its order number (emailed after payment, e.g. VIMP34456CB2). Not the ORD- reference from a pay link.",
        parameters={"type": "object", "properties": {
            "order_number": _p("string", "Kapruka order number."),
        }, "required": ["order_number"]},
    ),
    types.FunctionDeclaration(
        name="remember",
        description="Save facts about what the customer wants so you never ask twice. Call it (alongside other tools) whenever they state a budget, city, date, occasion, who it's for, a preference, or reject a product.",
        parameters={"type": "object", "properties": {
            "budget": _p("number", "Maximum budget in their currency."),
            "city": _p("string", "Delivery city."),
            "delivery_date": _p("string", "Wanted delivery date YYYY-MM-DD."),
            "occasion": _p("string", "birthday, anniversary, apology, avurudu, wedding, sympathy, get well, newborn, corporate, everyday..."),
            "recipient": _p("string", "Who it's for (e.g. 'wife', 'amma', 'myself', 'team at office')."),
            "notes": _p("string", "One short fact worth keeping (e.g. 'sister loves lilies', 'no chocolate - diabetic')."),
            "preferred_language": _p("string", "english, sinhala, singlish, tamil or tanglish."),
            "currency": _p("string", "LKR, USD, GBP, AUD, CAD or EUR."),
            "rejected_product_ids": _p("array", "Product IDs the customer said no to.", items={"type": "string"}),
        }},
    ),
    types.FunctionDeclaration(
        name="update_cart",
        description="Add a product to the customer's order, change its quantity, or remove it (quantity 0). Only for product IDs returned by Kapruka in this chat.",
        parameters={"type": "object", "properties": {
            "product_id": _p("string", "Product ID from search/get_product."),
            "quantity": _p("integer", "New quantity 0-99 (0 removes). Default 1."),
            "icing_text": _p("string", "Cake icing text, max 120 chars (cakes only)."),
        }, "required": ["product_id"]},
    ),
    types.FunctionDeclaration(
        name="prepare_order",
        description="Validate delivery details, re-check stock, price and delivery for every cart item, and show the customer a summary card with Yes/Edit buttons. Required before place_order.",
        parameters={"type": "object", "properties": {
            "recipient": {"type": "object", "properties": {
                "name": _p("string", "Recipient name."),
                "phone": _p("string", "Recipient phone, 07XXXXXXXX or +947XXXXXXXX."),
            }, "required": ["name", "phone"]},
            "delivery": {"type": "object", "properties": {
                "address": _p("string", "Street address."),
                "city": _p("string", "Delivery city."),
                "date": _p("string", "YYYY-MM-DD."),
                "location_type": _p("string", "house (default), apartment, office or other."),
                "instructions": _p("string", "Optional, max 250 chars."),
            }, "required": ["address", "city", "date"]},
            "sender": {"type": "object", "properties": {
                "name": _p("string", "Sender name for the gift card (the customer)."),
                "anonymous": _p("boolean", "Show 'Anonymous' on the card."),
            }, "required": ["name"]},
            "gift_message": _p("string", "Optional gift card message, max 300 chars."),
            "currency": _p("string", "LKR (default), USD, GBP, AUD, CAD or EUR."),
        }, "required": ["recipient", "delivery", "sender"]},
    ),
    types.FunctionDeclaration(
        name="place_order",
        description="Create the order from the confirmed summary and get the pay link. Only after the customer explicitly confirmed the summary card in their latest message.",
    ),
    types.FunctionDeclaration(
        name="reorder",
        description="'Same as last time': put the items of a previous order back in the cart (stock re-checked). Uses the given order number, or the last order from this chat or their previous visit.",
        parameters={"type": "object", "properties": {
            "order_number": _p("string", "Kapruka order number, if the customer gave one."),
        }},
    ),
]

TOOLS = [types.Tool(function_declarations=DECLARATIONS)]


def mask_phone(phone: str | None) -> str:
    digits = re.sub(r"\D", "", phone or "")
    return f"{digits[:3]}•••••{digits[-2:]}" if len(digits) >= 7 else "•••"


def normalize_phone(phone: str | None) -> str | None:
    raw = re.sub(r"[\s\-().]", "", phone or "")
    if re.fullmatch(r"\+94\d{9}", raw) or re.fullmatch(r"0\d{9}", raw):
        return raw
    if re.fullmatch(r"94\d{9}", raw):
        return "+" + raw
    if re.fullmatch(r"7\d{8}", raw):
        return "0" + raw
    return None


def _parse_date(value: str | None) -> date | None:
    try:
        return date.fromisoformat((value or "").strip())
    except ValueError:
        return None


def _cart_event(session: Session) -> dict:
    return {"type": "cart", "cart": session.cart_view()}


def order_lines(data: Any) -> list[dict]:
    """Pull product lines out of a tracked order (shape varies), for reordering."""
    if not isinstance(data, dict):
        return []
    for container in (data, data.get("order") if isinstance(data.get("order"), dict) else {}):
        for key in ("items", "cart", "products", "lines"):
            lines = container.get(key)
            if isinstance(lines, list):
                out = []
                for item in lines:
                    if not isinstance(item, dict):
                        continue
                    pid = item.get("product_id") or item.get("id") or item.get("sku") or item.get("code")
                    if pid:
                        out.append({
                            "product_id": str(pid),
                            "name": item.get("name") or item.get("product_name") or item.get("title"),
                            "quantity": int(item.get("quantity") or item.get("qty") or 1),
                        })
                return out
    return []


def _set_cart_line(session: Session, product: dict, quantity: int, icing_text: str | None = None) -> None:
    for line in session.cart:
        if line["product_id"].lower() == product["id"].lower():
            if quantity <= 0:
                session.cart.remove(line)
            else:
                line["quantity"] = quantity
                if icing_text is not None:
                    line["icing_text"] = icing_text
            return
    if quantity > 0:
        line = {
            "product_id": product["id"],
            "name": product.get("name"),
            "price": product.get("price"),
            "currency": product.get("currency", "LKR"),
            "quantity": quantity,
            "image": product.get("image"),
        }
        if icing_text:
            line["icing_text"] = icing_text
        session.cart.append(line)


async def search_products(session: Session, **args) -> Result:
    q = (args.get("q") or "").strip()
    if len(q) < 3:
        return {"error": "query_too_short", "message": "Use at least 3 characters of specific product words."}, []
    args["q"] = q
    args["limit"] = max(1, min(int(args.get("limit") or 6), 12))
    args.setdefault("in_stock_only", True)
    args.setdefault("currency", session.memory.get("currency"))
    result = await call_tool("search_products", args)
    relaxed = []
    for keys, label in ((("category",), "category"), (("min_price", "max_price"), "price")):
        if "error" in result or result.get("results"):
            break
        if any(args.get(k) is not None for k in keys):
            args = {k: v for k, v in args.items() if k not in keys}
            relaxed.append(label)
            result = await call_tool("search_products", args)
    if "error" in result:
        return result, []
    items = [normalize_product(r) for r in result.get("results", [])]
    session.add_products(items)
    out = compact_for_model("search_products", result)
    if relaxed and items:
        out["relaxed_filters"] = relaxed
        out["note"] = f"No exact matches, so these ignore the {' and '.join(relaxed)} filter. Tell the customer honestly."
    if not items:
        out["hint"] = "Nothing found. Try a different specific phrase (e.g. 'ribbon cake', 'chocolate cake', 'rose bouquet')."
    return out, [{"type": "products", "items": items}] if items else []


async def get_product(session: Session, product_id: str = "", currency: str | None = None) -> Result:
    result = await call_tool("get_product", {"product_id": product_id, "currency": currency or session.memory.get("currency")})
    if "error" in result:
        return result, []
    item = normalize_product(result)
    session.add_products([item])
    return compact_for_model("get_product", result), [{"type": "products", "items": [item]}]


async def list_delivery_cities(session: Session, query: str | None = None, limit: int | None = None) -> Result:
    return await call_tool("list_delivery_cities", {"query": query, "limit": limit or 10}), []


async def check_delivery(session: Session, city: str = "", delivery_date: str | None = None, product_id: str | None = None) -> Result:
    canonical, suggestions = await resolve_city(city)
    if not canonical:
        return {"error": "unknown_city", "message": f"'{city}' is not a Kapruka delivery city.", "did_you_mean": suggestions}, []
    args = {"city": canonical, "delivery_date": delivery_date, "product_id": product_id}
    result = await call_tool("check_delivery", args)
    if "error" in result:
        return result, []
    wanted = _parse_date(delivery_date)
    if result.get("available") is False and wanted:
        for offset in range(1, 4):
            nxt = (wanted + timedelta(days=offset)).isoformat()
            probe = await call_tool("check_delivery", {**args, "delivery_date": nxt})
            if probe.get("available"):
                result = {**result, "next_available_date": nxt, "next_available_rate": probe.get("rate")}
                break
    product = session.product(product_id) if product_id else None
    session.delivery_checks.append({**result, "product_id": product_id})
    del session.delivery_checks[:-10]
    event = {"type": "delivery", "data": {**result, "product_name": product.get("name") if product else None}}
    return result, [event]


async def track_order(session: Session, order_number: str = "") -> Result:
    order_number = order_number.strip().upper()
    result = await call_tool("track_order", {"order_number": order_number}, use_cache=False)
    if "error" in result:
        return result, []
    if order_number not in session.order_numbers:
        session.order_numbers.append(order_number)
    return result, [{"type": "tracking", "order_number": order_number, "data": result}]


async def remember(session: Session, **values) -> Result:
    session.remember(**values)
    if values.get("preferred_language"):
        session.language = values["preferred_language"]
    return {"saved": True, "memory": session.memory}, [{"type": "memory", "memory": session.memory}]


async def update_cart(session: Session, product_id: str = "", quantity: int | None = None, icing_text: str | None = None) -> Result:
    product = session.product(product_id)
    if not product:
        return {"error": "unknown_product", "message": "Only products returned by Kapruka in this chat can be ordered. Search or get_product first."}, []
    quantity = 1 if quantity is None else max(0, min(int(quantity), 99))
    if quantity > 0 and product.get("in_stock") is False:
        return {"error": "out_of_stock", "message": f"{product['name']} is out of stock. Offer alternatives (ask before swapping)."}, []
    if icing_text and len(icing_text) > 120:
        return {"error": "icing_too_long", "message": "Icing text must be 120 characters or less."}, []
    if quantity > 0 and len(session.cart) >= 30 and not any(l["product_id"].lower() == product_id.lower() for l in session.cart):
        return {"error": "cart_full", "message": "The cart can hold at most 30 different items."}, []
    _set_cart_line(session, product, quantity, icing_text)
    if session.pending_order and session.pending_order["cart_hash"] != session.cart_hash():
        session.pending_order = None
    return {"cart": session.cart_view()}, [_cart_event(session)]


def _validate_details(session: Session, recipient: dict, delivery: dict, sender: dict, gift_message: str | None) -> list[str]:
    issues = []
    if not session.cart:
        issues.append("The cart is empty - add products with update_cart first.")
    if not (recipient.get("name") or "").strip() or len(recipient.get("name", "")) > 80:
        issues.append("Recipient name is required (max 80 characters).")
    if not normalize_phone(recipient.get("phone")):
        issues.append("Recipient phone must be a Sri Lankan number like 0771234567 or +94771234567.")
    if not (delivery.get("address") or "").strip() or len(delivery.get("address", "")) > 250:
        issues.append("Street address is required (max 250 characters).")
    if not (delivery.get("city") or "").strip():
        issues.append("Delivery city is required.")
    wanted = _parse_date(delivery.get("date"))
    if not wanted:
        issues.append("Delivery date is required as YYYY-MM-DD.")
    elif wanted < colombo_now().date():
        issues.append("Delivery date is in the past (Sri Lanka time).")
    if (delivery.get("location_type") or "house").lower() not in LOCATION_TYPES:
        issues.append("Location type must be house, apartment, office or other.")
    if len(delivery.get("instructions") or "") > 250:
        issues.append("Delivery instructions must be 250 characters or less.")
    if not (sender.get("name") or "").strip() or len(sender.get("name", "")) > 80:
        issues.append("Sender name is required for the gift card (max 80 characters).")
    if len(gift_message or "") > 300:
        issues.append("Gift message must be 300 characters or less.")
    return issues


async def prepare_order(session: Session, recipient: dict | None = None, delivery: dict | None = None,
                        sender: dict | None = None, gift_message: str | None = None, currency: str | None = None) -> Result:
    recipient, delivery, sender = dict(recipient or {}), dict(delivery or {}), dict(sender or {})
    issues = _validate_details(session, recipient, delivery, sender, gift_message)
    if issues:
        return {"error": "missing_or_invalid_details", "issues": issues, "hint": "Ask the customer for exactly these, in one message."}, []

    city, suggestions = await resolve_city(delivery["city"])
    if not city:
        return {"error": "unknown_city", "message": f"'{delivery['city']}' is not a Kapruka delivery city.", "did_you_mean": suggestions}, []
    when = delivery["date"].strip()
    currency = currency or session.memory.get("currency") or session.cart[0].get("currency") or "LKR"
    semaphore = asyncio.Semaphore(4)

    async def recheck(line: dict):
        async with semaphore:
            product = await call_tool("get_product", {"product_id": line["product_id"], "currency": currency}, use_cache=False)
            check = await call_tool("check_delivery", {"city": city, "delivery_date": when, "product_id": line["product_id"]}, use_cache=False)
        return line, product, check

    problems, warnings, fee = [], [], 0.0
    for line, product, check in await asyncio.gather(*(recheck(line) for line in session.cart)):
        if "error" in product:
            problems.append(f"{line['name']}: {product.get('message', 'could not be re-checked')}")
            continue
        if product.get("in_stock") is False:
            problems.append(f"{line['name']} just went out of stock.")
        fresh = normalize_product(product)
        if fresh["price"] is not None and line.get("price") is not None and abs(fresh["price"] - line["price"]) > 0.01:
            warnings.append(f"{line['name']} price changed from {line['price']:,.0f} to {fresh['price']:,.0f} {fresh['currency']}.")
        line["price"], line["currency"] = fresh["price"], fresh["currency"]
        if "error" in check:
            problems.append(f"Delivery check failed for {line['name']}: {check.get('message')}")
        elif not check.get("available"):
            problems.append(f"{line['name']} can't be delivered to {city} on {when}.")
        else:
            fee = max(fee, float(check.get("rate") or 0))
            if check.get("perishable_warning"):
                warnings.append(f"{line['name']}: {check['perishable_warning']}")
    if problems:
        return {"error": "cannot_fulfil", "problems": problems,
                "hint": "Tell the customer exactly which item blocks the order; offer another date, city, or a swap. Never substitute without asking."}, [_cart_event(session)]

    cart = session.cart_view()
    summary = {
        "items": [{**line, "line_total": round((line["price"] or 0) * line["quantity"], 2)} for line in session.cart],
        "subtotal": cart["subtotal"],
        "currency": cart["currency"],
        "delivery_fee": fee,
        "delivery_fee_currency": "LKR",
        "estimated_total": round(cart["subtotal"] + fee, 2) if cart["currency"] == "LKR" else None,
        "recipient": {"name": recipient["name"].strip(), "phone": normalize_phone(recipient["phone"])},
        "delivery": {
            "address": delivery["address"].strip(),
            "city": city,
            "date": when,
            "location_type": (delivery.get("location_type") or "house").lower(),
            "instructions": (delivery.get("instructions") or "").strip() or None,
        },
        "sender": {"name": sender["name"].strip(), "anonymous": bool(sender.get("anonymous"))},
        "gift_message": (gift_message or "").strip() or None,
        "warnings": warnings,
    }
    payload = {
        "cart": [
            {"product_id": l["product_id"], "quantity": l["quantity"], **({"icing_text": l["icing_text"]} if l.get("icing_text") else {})}
            for l in session.cart
        ],
        "recipient": summary["recipient"],
        "delivery": {k: v for k, v in summary["delivery"].items() if v is not None},
        "sender": summary["sender"],
        "currency": currency,
    }
    if summary["gift_message"]:
        payload["gift_message"] = summary["gift_message"]
    session.pending_order = {"payload": payload, "summary": summary, "turn": session.turn, "cart_hash": session.cart_hash()}
    session.remember(city=city, delivery_date=when)

    for_model = {**summary, "recipient": {**summary["recipient"], "phone": mask_phone(summary["recipient"]["phone"])}}
    return {
        "status": "summary_shown_awaiting_confirmation",
        "summary": for_model,
        "next": "A summary card with 'Yes, place order' and 'Edit' buttons is on screen. In 1-2 sentences ask them to check it. Do NOT call place_order in this turn.",
    }, [{"type": "order_summary", "summary": summary}]


async def place_order(session: Session) -> Result:
    pending = session.pending_order
    if not pending:
        return {"error": "no_summary", "message": "Call prepare_order first so the customer sees and confirms the summary."}, []
    if pending["turn"] >= session.turn:
        return {"error": "not_confirmed_yet", "message": "The customer has only just seen the summary. Wait for their confirmation in their next message."}, []
    if pending["cart_hash"] != session.cart_hash():
        session.pending_order = None
        return {"error": "cart_changed", "message": "The cart changed after the summary. Call prepare_order again."}, []
    if len([o for o in session.orders if time() - o["created"] < 3600]) >= MAX_ORDERS_PER_HOUR:
        return {"error": "order_limit", "message": "Too many orders from this chat in the last hour. Ask them to finish paying the existing link first."}, [{"type": "order_failed"}]

    result = await call_tool("create_order", pending["payload"], use_cache=False)
    if "error" in result or not result.get("checkout_url"):
        code = result.get("error", "unknown")
        return {"error": code, "message": result.get("message") or result.get("text"),
                "hint": ORDER_ERROR_HINTS.get(code, "Explain simply and offer to fix the details.")}, [{"type": "order_failed", "message": result.get("message")}]

    summary = pending["summary"]
    totals = result.get("summary") or {}
    order = {
        "order_ref": result.get("order_ref"),
        "checkout_url": result["checkout_url"],
        "expires_at": result.get("expires_at"),
        "totals": totals,
        "items": [{"product_id": i["product_id"], "name": i["name"], "quantity": i["quantity"], "image": i.get("image")} for i in summary["items"]],
        "city": summary["delivery"]["city"],
        "date": summary["delivery"]["date"],
        "recipient_name": summary["recipient"]["name"],
    }
    session.orders.append({
        "order_ref": order["order_ref"],
        "items": [{"product_id": i["product_id"], "name": i["name"], "quantity": i["quantity"]} for i in summary["items"]],
        "city": order["city"],
        "grand_total": totals.get("grand_total"),
        "created": time(),
    })
    session.cart, session.pending_order = [], None
    return {
        "status": "payment_link_ready",
        "order_ref": order["order_ref"],
        "grand_total": totals.get("grand_total"),
        "currency": totals.get("currency"),
        "expires_at": order["expires_at"],
        "next": "The pay card is on screen. Tell them: pay within 60 minutes (prices locked); Kapruka emails the order number after payment, which you can use to track it.",
    }, [{"type": "order", "data": order}, _cart_event(session)]


async def reorder(session: Session, order_number: str | None = None) -> Result:
    if order_number:
        tracked = await call_tool("track_order", {"order_number": order_number.strip().upper()}, use_cache=False)
        if "error" in tracked:
            return tracked, []
        lines = order_lines(tracked)
    elif session.orders:
        lines = session.orders[-1]["items"]
    else:
        lines = (session.memory.get("last_order") or {}).get("items", [])
    if not lines:
        return {"error": "nothing_to_reorder", "message": "No previous order found. Ask for their Kapruka order number from the confirmation email."}, []

    added, unavailable, items = [], [], []
    for line in lines[:30]:
        product = await call_tool("get_product", {"product_id": line["product_id"]})
        if "error" in product or product.get("in_stock") is False:
            unavailable.append(line.get("name") or line["product_id"])
            continue
        item = normalize_product(product)
        items.append(item)
        _set_cart_line(session, item, int(line.get("quantity") or 1))
        added.append(f"{line.get('quantity') or 1} x {item['name']} ({item['id']})")
    session.add_products(items)
    return {"added": added, "unavailable": unavailable, "cart": session.cart_view()}, [
        {"type": "products", "items": items}, _cart_event(session)]


HANDLERS = {
    "search_products": search_products,
    "get_product": get_product,
    "list_delivery_cities": list_delivery_cities,
    "check_delivery": check_delivery,
    "track_order": track_order,
    "remember": remember,
    "update_cart": update_cart,
    "prepare_order": prepare_order,
    "place_order": place_order,
    "reorder": reorder,
}


async def run_tool(session: Session, name: str, args: dict) -> Result:
    handler = HANDLERS.get(name)
    if not handler:
        return {"error": "unknown_tool", "message": f"Unknown tool: {name}"}, []
    try:
        return await handler(session, **args)
    except TypeError as e:
        return {"error": "bad_arguments", "message": str(e)}, []


async def apply_ui_action(session: Session, action: dict | None) -> tuple[str, list[dict]]:
    """Apply a button tap from the UI. Returns a note for the model and events for the UI."""
    if not action:
        return "", []
    kind = action.get("type")
    product = session.product(action.get("product_id", "")) if action.get("product_id") else None

    if kind == "select_product" and product:
        return f"[The customer tapped 'Choose this' on {product['name']} (id {product['id']}).]", []
    if kind == "product_details" and product:
        return f"[The customer tapped 'Details' on {product['name']} (id {product['id']}). Use get_product and describe it briefly.]", []
    if kind == "remove_from_cart" and product:
        _set_cart_line(session, product, 0)
        if session.pending_order and session.pending_order["cart_hash"] != session.cart_hash():
            session.pending_order = None
        return f"[The customer removed {product['name']} from the cart using the cart button.]", [_cart_event(session)]
    if kind == "confirm_order":
        result, events = await place_order(session)
        return f"[The customer tapped 'Yes, place order' on the summary card. place_order was run for them. Result: {result}]", events
    if kind == "set_preferences":
        prefs = action.get("preferences") or {}
        allowed = {k: prefs[k] for k in ("budget", "city", "delivery_date", "recipient", "occasion") if prefs.get(k)}
        session.remember(**allowed)
        return f"[Quick plan filled in by the customer: {allowed}]", [{"type": "memory", "memory": session.memory}]
    if kind == "paid":
        return f"[The customer says they paid for {action.get('order_ref') or 'their order'}.]", []
    return "", []
