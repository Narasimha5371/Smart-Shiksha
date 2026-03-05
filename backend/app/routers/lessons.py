"""
Lesson-related API routes.

Endpoints:
  POST /api/ask               → RAG pipeline: question → AI lesson (auth required)
  POST /api/ask-with-file     → RAG pipeline with image/file upload (auth required)
  POST /api/lessons/save      → Persist a lesson for offline access (auth required)
  GET  /api/lessons/mine      → List saved lessons for the current user (auth required)
"""

import base64
import logging

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
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
logger = logging.getLogger(__name__)

# Allowed image MIME types and max file size (5 MB)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_TEXT_TYPES = {"text/plain", "application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


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
#  POST /api/ask-with-file  — question + image/file upload (auth required)
# ──────────────────────────────────────────────

@router.post("/ask-with-file", response_model=AskResponse)
@limiter.limit(settings.RATE_LIMIT_ASK)
async def ask_with_file(
    request: Request,
    question: str = Form(..., min_length=3, max_length=1000),
    target_language: str = Form(default="en"),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
) -> AskResponse:
    """
    Accept a student's question + uploaded image or text file.
    Analyze the file content (vision model for images, text extraction for docs)
    and run the full RAG pipeline with extra context.
    """
    # Validate file type
    content_type = file.content_type or ""
    is_image = content_type in ALLOWED_IMAGE_TYPES
    is_text = content_type in ALLOWED_TEXT_TYPES

    if not is_image and not is_text:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. "
                   f"Allowed: images (JPEG, PNG, GIF, WebP) and text files (.txt).",
        )

    # Read file data
    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(file_data) / 1024 / 1024:.1f} MB). Max: 5 MB.",
        )

    image_base64 = None
    image_mime = None
    file_text = None

    if is_image:
        image_base64 = base64.b64encode(file_data).decode("utf-8")
        image_mime = content_type
        logger.info("Processing image upload: %s (%s, %d bytes)", file.filename, content_type, len(file_data))
    elif is_text:
        try:
            file_text = file_data.decode("utf-8")
        except UnicodeDecodeError:
            file_text = file_data.decode("latin-1", errors="replace")
        logger.info("Processing text upload: %s (%d chars)", file.filename, len(file_text))

    try:
        result = await rag_pipeline.generate_lesson_with_file(
            question=question,
            target_language=target_language,
            image_base64=image_base64,
            image_mime=image_mime or "image/jpeg",
            file_text=file_text,
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
