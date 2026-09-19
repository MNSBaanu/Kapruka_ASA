import re
from itertools import combinations
from app.core.actions import mask_phone
from app.core.state import Session

MARKER = re.compile(r"\[\[product:([A-Za-z0-9_\-]+)\]\]")
MONEY = re.compile(r"(?:LKR|Rs\.?|රු\.?|USD|US\$|GBP|£|EUR|€|AUD|CAD)\s?(\d[\d,]*(?:\.\d+)?)", re.I)
MONEY_AFTER = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s?(?:LKR|rupees|/-)", re.I)
NUMBER = re.compile(r"(\d[\d,]*(?:\.\d+)?)\s*(k)?\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+94|0)7\d[\s-]?\d{3}[\s-]?\d{4}(?!\d)")
DELIVERY_CLAIM = re.compile(r"\b(today|tomorrow|tonight|same[- ]day|heta|ada)\b|අද|හෙට|இன்று|நாளை", re.I)
OUT_OF_STOCK_WORDS = re.compile(r"out of stock|sold out|not in stock|unavailable|stock නැ|ඉවරයි|இருப்பு இல்லை|stock illa|stock naha", re.I)


def _to_number(raw: str, k: str | None = None) -> float | None:
    try:
        value = float(raw.replace(",", ""))
    except ValueError:
        return None
    return value * 1000 if k else value


def known_amounts(session: Session, user_text: str) -> list[float]:
    """Every money figure the reply may legitimately mention: tool data, cart maths, user-stated numbers."""
    amounts: set[float] = set()
    prices = []
    for p in session.products.values():
        prices.append(p.get("price"))
        amounts.add(p.get("compare_at_price"))
        amounts.update(v.get("price") for v in p.get("variants") or [])
    prices = [p for p in prices if isinstance(p, (int, float))]
    amounts.update(prices)
    amounts.update(p * q for p in prices for q in range(2, 11))
    amounts.update(a + b for a, b in combinations(prices[-24:], 2))
    for check in session.delivery_checks:
        amounts.update((check.get("rate"), check.get("next_available_rate")))
    lines = [l["price"] * l["quantity"] for l in session.cart if l.get("price") is not None]
    amounts.update(lines)
    amounts.add(sum(lines))
    fee = max((c.get("rate") or 0 for c in session.delivery_checks), default=0)
    amounts.add(sum(lines) + fee)
    if session.pending_order:
        s = session.pending_order["summary"]
        amounts.update((s["subtotal"], s["delivery_fee"], s["estimated_total"]))
    for order in session.orders:
        amounts.add(order.get("grand_total"))
    for key in ("budget",):
        amounts.add(session.memory.get(key))
    for content in session.contents:
        for part in content.parts or []:
            if part.function_call and part.function_call.args:
                amounts.update(v for v in part.function_call.args.values() if isinstance(v, (int, float)))
            if part.text and content.role == "user":
                amounts.update(_to_number(n, k) for n, k in NUMBER.findall(part.text))
    amounts.update(_to_number(n, k) for n, k in NUMBER.findall(user_text))
    return [a for a in amounts if isinstance(a, (int, float)) and a > 0]


def _price_ok(amount: float, known: list[float]) -> bool:
    return amount < 100 or any(abs(amount - k) <= max(1.0, 0.02 * k) for k in known)


def verify(text: str, session: Session, user_text: str = "") -> tuple[str, list[str]]:
    """Check a reply before the customer relies on it. Returns (cleaned text, problems needing a rewrite)."""
    issues: list[str] = []
    clean = text

    for pid in dict.fromkeys(MARKER.findall(text)):
        product = session.product(pid)
        if not product:
            clean = re.sub(rf"[ \t]*\[\[product:{re.escape(pid)}\]\][ \t]*\n?", "", clean)
        elif product.get("in_stock") is False and not OUT_OF_STOCK_WORDS.search(text):
            issues.append(f"You showed {product['name']} but it is out of stock and you didn't say so.")

    known = known_amounts(session, user_text)
    for raw in dict.fromkeys(MONEY.findall(clean) + MONEY_AFTER.findall(clean)):
        amount = _to_number(raw)
        if amount is not None and not _price_ok(amount, known):
            issues.append(f"The amount {raw} doesn't match any Kapruka price, fee or total in this chat.")

    clean = PHONE.sub(lambda m: mask_phone(m.group(0)), clean)
    return clean, issues


def mentioned_products(text: str, session: Session, candidate_ids: list[str]) -> list[str]:
    """Products the reply talks about by name without markers, so their cards can still be shown."""
    lowered = text.lower()
    found = []
    for pid in dict.fromkeys(candidate_ids):
        product = session.product(pid)
        name = (product or {}).get("name") or ""
        if len(name) >= 6 and name.lower() in lowered:
            found.append(product["id"])
    return found[:4]


def unverified_delivery(text: str, session: Session) -> bool:
    """True when the reply shows products and talks about delivery timing that no check_delivery has backed up."""
    shown = {pid.lower() for pid in MARKER.findall(text)}
    if not shown or not DELIVERY_CLAIM.search(MARKER.sub("", text)):
        return False
    checked = {(c.get("product_id") or "").lower() for c in session.delivery_checks}
    return not shown & checked
