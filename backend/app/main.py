import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.core.catalog import warm_up
from app.mcp.client import mcp_client

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("kapruka")


async def _warm_up() -> None:
    try:
        await warm_up()
    except Exception as e:
        log.warning("MCP warm-up failed: %s", type(e).__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    warm = asyncio.create_task(_warm_up())
    yield
    warm.cancel()
    await mcp_client.close()


app = FastAPI(title="Kapruka ASA", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials="*" not in settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")

if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        return HTMLResponse(content=(FRONTEND_DIST / "index.html").read_text(encoding="utf-8"))

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = (FRONTEND_DIST / full_path).resolve()
        if file_path.is_file() and FRONTEND_DIST.resolve() in file_path.parents:
            return FileResponse(str(file_path))
        return HTMLResponse(content=(FRONTEND_DIST / "index.html").read_text(encoding="utf-8"))
else:
    @app.get("/")
    async def frontend_missing():
        return HTMLResponse(
            "<h1>Kapruka ASA</h1><p>The frontend isn't built yet. Run <code>npm run build</code> in <code>frontend/</code> "
            "(or <code>bash run.sh</code>), then restart the server.</p>",
            status_code=503,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
