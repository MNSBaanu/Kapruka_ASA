from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.mcp.client import mcp_client

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mcp_client.initialize()
    yield
    await mcp_client.close()


app = FastAPI(title="Kapruka ASA", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router, prefix="/api")

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return HTMLResponse(content=(FRONTEND_DIST / "index.html").read_text(encoding="utf-8"))

    @app.get("/favicon.svg")
    async def serve_favicon():
        return FileResponse(str(FRONTEND_DIST / "favicon.svg"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = FRONTEND_DIST / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return HTMLResponse(content=(FRONTEND_DIST / "index.html").read_text(encoding="utf-8"))
