from dataclasses import dataclass, field
from os import getenv
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = field(default_factory=lambda: getenv("GEMINI_API_KEY", ""))
    gemini_model: str = getenv("GEMINI_MODEL", "models/gemini-1.5-flash-latest")
    mcp_endpoint: str = getenv("MCP_ENDPOINT", "https://mcp.kapruka.com/mcp")
    mcp_timeout: int = int(getenv("MCP_TIMEOUT", "30"))
    cache_ttl_seconds: int = int(getenv("CACHE_TTL_SECONDS", "120"))
    max_history: int = int(getenv("MAX_HISTORY", "50"))
    app_port: int = int(getenv("APP_PORT", "8000"))
    app_host: str = getenv("APP_HOST", "0.0.0.0")
    cors_origins: list[str] = field(default_factory=lambda: getenv("CORS_ORIGINS", "*").split(","))


settings = Settings()
