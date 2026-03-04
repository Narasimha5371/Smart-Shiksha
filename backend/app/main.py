"""
Smart Shiksha — FastAPI entry point.

Responsibilities:
  • CORS middleware (Flutter app + HTML portal)
  • Rate limiting via slowapi
  • Async lifespan: create DB tables on startup
  • Mount all API routers
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings, SUPPORTED_LANGUAGES
from app.database import init_db
from app.routers import auth, competitive, lessons, progress, quiz, syllabus, users

# ── Config & logging ──────────────────────────
settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger("smartsiksha")


# ── Lifespan (startup/shutdown) ──────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB migrations and seed data on startup; cleanup on shutdown."""
    logger.info("🚀 Starting Smart Shiksha backend…")
    await init_db()
    logger.info("✅ Database tables ensured.")

    # Seed curriculum and competitive-exam data
    from app.database import async_session_factory
    from app.services.syllabus_seed import seed_all
    async with async_session_factory() as session:
        await seed_all(session)

    yield
    logger.info("👋 Shutting down Smart Shiksha backend.")


# ── App instance ──────────────────────────────
app = FastAPI(
    title="Smart Shiksha API",
    description="Multilingual AI-powered educational platform for rural India",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Rate limiter ──────────────────────────────
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── CORS middleware ───────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────
app.include_router(auth.router)
app.include_router(lessons.router)
app.include_router(users.router)
app.include_router(syllabus.router)
app.include_router(quiz.router)
app.include_router(progress.router)
app.include_router(competitive.router)


# ── Health check ──────────────────────────────
@app.get("/api/health", tags=["system"])
async def health_check():
    return {"status": "healthy", "service": "Smart Shiksha API"}


@app.get("/api/languages", tags=["system"])
async def list_languages():
    """Return all supported languages for the frontend dropdowns."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    }
