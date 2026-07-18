"""SkillHub FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from skillhub.api.auth import router as auth_router
from skillhub.api.deps import get_config, get_db, get_storage
from skillhub.api.skills import router as skills_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: init DB and storage on startup, close on shutdown."""
    config = await get_config()
    db = await get_db(config)
    storage = await get_storage(config)
    yield
    await db.close()


app = FastAPI(
    title="SkillHub",
    description="A lightweight skill registry for Hermes Agent skills",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check (before static mount)
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "skillhub"}


# API routers
app.include_router(skills_router)
app.include_router(auth_router)

# Static files (Web UI) - mounted at /ui to not catch API routes
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="static")
