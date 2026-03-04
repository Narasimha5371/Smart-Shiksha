"""
Lesson-related API routes.

Endpoints:
  POST /api/ask               → RAG pipeline: question → AI lesson (auth required)
  POST /api/lessons/save      → Persist a lesson for offline access (auth required)
  GET  /api/lessons/mine      → List saved lessons for the current user (auth required)
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import SavedLesson, User
from app.schemas import (
    AskRequest,
    AskResponse,
    LessonResponse,
    SaveLessonRequest,
)
from app.services import rag_pipeline

settings = get_settings()
router = APIRouter(prefix="/api", tags=["lessons"])

limiter = Limiter(key_func=get_remote_address)


# ──────────────────────────────────────────────
#  POST /api/ask  — the main RAG endpoint (auth required)
# ──────────────────────────────────────────────

@router.post("/ask", response_model=AskResponse)
@limiter.limit(settings.RATE_LIMIT_ASK)
async def ask_question(
    request: Request,
    body: AskRequest = Body(...),
    user: User = Depends(get_current_user),
) -> AskResponse:
    """
    Accept a student's question + target language, run the full
    Serper → Groq RAG pipeline, and return a Markdown lesson.
    Requires authentication.
    """
    try:
        result = await rag_pipeline.generate_lesson(
            question=body.question,
            target_language=body.target_language,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return AskResponse(**result)


# ──────────────────────────────────────────────
#  POST /api/lessons/save (auth required, saves for current user)
# ──────────────────────────────────────────────

@router.post("/lessons/save", response_model=LessonResponse, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def save_lesson(
    request: Request,
    body: SaveLessonRequest = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LessonResponse:
    """Persist a generated lesson so the student can read it offline.
    Always saves under the authenticated user's ID (ignores body.user_id)."""
    lesson = SavedLesson(
        user_id=user.id,             # Always use the authenticated user
        topic=body.topic,
        content=body.content,
        language_code=body.language_code,
        source_urls=body.source_urls,
    )
    db.add(lesson)
    await db.flush()          # populate defaults before returning
    await db.refresh(lesson)
    return lesson              # Pydantic model_config from_attributes handles ORM→dict


# ──────────────────────────────────────────────
#  GET /api/lessons/mine  (auth required, own lessons only)
# ──────────────────────────────────────────────

@router.get("/lessons/mine", response_model=list[LessonResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_my_lessons(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LessonResponse]:
    """Return all saved lessons for the current authenticated user, newest first."""
    stmt = (
        select(SavedLesson)
        .where(SavedLesson.user_id == user.id)
        .order_by(SavedLesson.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


# ──────────────────────────────────────────────
#  GET /api/lessons/{user_id}  (auth required, ownership enforced)
# ──────────────────────────────────────────────

@router.get("/lessons/{user_id}", response_model=list[LessonResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_lessons(
    user_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LessonResponse]:
    """Return all saved lessons for a given user, newest first.
    Users can only access their own lessons."""
    if user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    stmt = (
        select(SavedLesson)
        .where(SavedLesson.user_id == user_id)
        .order_by(SavedLesson.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
