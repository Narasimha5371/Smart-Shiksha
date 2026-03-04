"""
Async SQLAlchemy engine & session factory.

Designed for instant SQLite ↔ PostgreSQL switching:
  - Dev:  DATABASE_URL = "sqlite+aiosqlite:///./smartsiksha.db"
  - Prod: DATABASE_URL = "postgresql+asyncpg://user:pass@host/smartsiksha"

Change *only* the DATABASE_URL in .env — zero code changes required.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

settings = get_settings()

# ---------- Engine ----------
# connect_args needed only for SQLite (check_same_thread is an SQLite-only arg)
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if _is_sqlite else {},
)

# ---------- Session factory ----------
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # prevents lazy-load errors in async
)


# ---------- Dependency for FastAPI ----------
async def get_db() -> AsyncSession:                         # type: ignore[misc]
    """Yield an async session and ensure it closes after the request."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------- Startup helper ----------
async def init_db() -> None:
    """Create all tables (safe to call repeatedly — uses IF NOT EXISTS)."""
    from app.models import Base                             # noqa: F811

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
