"""SkillHub FastAPI application."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from skillhub.api.deps import get_config, get_db, get_storage
from skillhub.api.skills import router as skills_router
from skillhub.api.auth import router as auth_router
from skillhub.api.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = await get_config()
    db = await get_db(config)
    storage = await get_storage(config)

    # U5: Create admin user from config preset if configured
    if config.admin.password_hash:
        existing_admin = await db.get_user_by_username(config.admin.username)
        if not existing_admin:
            await db.create_user(
                username=config.admin.username,
                password_hash=config.admin.password_hash,
                role="admin",
            )

    yield
    await db.close()


app = FastAPI(
    title="SkillHub",
    description="A lightweight skill registry for Hermes Agent skills",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "skillhub"}


app.include_router(skills_router)
app.include_router(auth_router)
app.include_router(users_router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="static")
