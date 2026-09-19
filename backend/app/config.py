from dataclasses import dataclass, field
from os import getenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def _optional_int(name: str) -> int | None:
    value = getenv(name, "").strip()
    return int(value) if value else None


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default_factory=lambda: getenv("GEMINI_API_KEY", ""))
    gemini_model: str = getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
    gemini_thinking_budget: int | None = _optional_int("GEMINI_THINKING_BUDGET")
    mcp_endpoint: str = getenv("MCP_ENDPOINT", "https://mcp.kapruka.com/mcp")
    mcp_timeout: int = int(getenv("MCP_TIMEOUT", "30"))
    cache_ttl_seconds: int = int(getenv("CACHE_TTL_SECONDS", "900"))
    delivery_cache_ttl_seconds: int = int(getenv("DELIVERY_CACHE_TTL_SECONDS", "60"))
    max_history: int = int(getenv("MAX_HISTORY", "40"))
    session_ttl_seconds: int = int(getenv("SESSION_TTL_SECONDS", "86400"))
    max_sessions: int = int(getenv("MAX_SESSIONS", "2000"))
    chat_rate_per_minute: int = int(getenv("CHAT_RATE_PER_MINUTE", "20"))
    app_port: int = int(getenv("PORT", getenv("APP_PORT", "8000")))
    app_host: str = getenv("APP_HOST", "0.0.0.0")
    cors_origins: list[str] = field(default_factory=lambda: [o.strip() for o in getenv("CORS_ORIGINS", "*").split(",") if o.strip()])


settings = Settings()
