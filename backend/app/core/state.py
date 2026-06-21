from typing import Any
from app.config import settings


class Session:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history: list[dict[str, str]] = []
        self.context: dict[str, Any] = {}

    def add_message(self, role: str, content: str) -> None:
        self.history.append({"role": role, "content": content})
        if len(self.history) > settings.max_history:
            self.history = self.history[-settings.max_history:]

    def set_context(self, key: str, value: Any) -> None:
        self.context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)

    def clear_context(self) -> None:
        self.context.clear()


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def get_or_create(self, session_id: str) -> Session:
        if session_id not in self._sessions:
            self._sessions[session_id] = Session(session_id)
        return self._sessions[session_id]

    def remove(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


session_store = SessionStore()
