import asyncio
import hashlib
import json
from time import time
from typing import Any
from google.genai import types
from app.config import settings


def is_user_text(content: types.Content) -> bool:
    parts = content.parts or []
    return content.role == "user" and any(p.text for p in parts) and not any(p.function_response for p in parts)


class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.contents: list[types.Content] = []
        self.memory: dict[str, Any] = {}
        self.language = "english"
        self.products: dict[str, dict] = {}
        self.cart: list[dict] = []
        self.delivery_checks: list[dict] = []
        self.pending_order: dict | None = None
        self.orders: list[dict] = []
        self.order_numbers: list[str] = []
        self.turn = 0
        self.last_active = time()
        self.lock = asyncio.Lock()

    def add_content(self, content: types.Content) -> None:
        self.contents.append(content)

    def trim_history(self) -> None:
        if len(self.contents) <= settings.max_history:
            return
        start = len(self.contents) - settings.max_history
        while start < len(self.contents) and not is_user_text(self.contents[start]):
            start += 1
        self.contents = self.contents[start:]

    def remember(self, **values: Any) -> None:
        for key, value in values.items():
            if value in (None, "", []):
                continue
            if key == "notes":
                notes = self.memory.setdefault("notes", [])
                if value not in notes:
                    notes.append(value)
                    del notes[:-8]
            elif key == "rejected_product_ids":
                rejected = self.memory.setdefault("rejected_product_ids", [])
                rejected.extend(v for v in value if v not in rejected)
            else:
                self.memory[key] = value

    def add_products(self, items: list[dict]) -> None:
        for item in items:
            if item.get("id"):
                self.products[item["id"].lower()] = {**self.products.get(item["id"].lower(), {}), **item}

    def product(self, product_id: str) -> dict | None:
        return self.products.get((product_id or "").lower())

    def cart_view(self) -> dict:
        currency = self.cart[0]["currency"] if self.cart else "LKR"
        subtotal = sum(line["price"] * line["quantity"] for line in self.cart if line.get("price") is not None)
        return {
            "items": self.cart,
            "count": sum(line["quantity"] for line in self.cart),
            "subtotal": round(subtotal, 2),
            "currency": currency,
        }

    def cart_hash(self) -> str:
        key = [(line["product_id"], line["quantity"], line.get("icing_text")) for line in self.cart]
        return hashlib.sha1(json.dumps(key).encode()).hexdigest()


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str) -> Session:
        self._evict()
        session = self._sessions.get(session_id)
        if session is None:
            session = self._sessions[session_id] = Session(session_id)
        session.last_active = time()
        return session

    def _evict(self) -> None:
        cutoff = time() - settings.session_ttl_seconds
        for sid in [sid for sid, s in self._sessions.items() if s.last_active < cutoff]:
            del self._sessions[sid]
        if len(self._sessions) >= settings.max_sessions:
            oldest = sorted(self._sessions.values(), key=lambda s: s.last_active)
            for s in oldest[: len(self._sessions) - settings.max_sessions + 1]:
                del self._sessions[s.session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


session_store = SessionStore()
