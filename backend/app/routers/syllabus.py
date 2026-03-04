"""
Syllabus API routes.

Endpoints:
  GET /api/syllabus/curricula           → list all curricula
  GET /api/syllabus/subjects            → subjects for curriculum+class+stream
  GET /api/syllabus/chapters/{sub_id}   → chapters for a subject
  GET /api/syllabus/lessons/{ch_id}     → generated lessons for a chapter
  POST /api/syllabus/generate/{ch_id}   → generate lesson content via AI
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Chapter, GeneratedLesson, Subject, User
from app.schemas import (
    ChapterResponse,
    GeneratedLessonResponse,
    SubjectResponse,
)
from app.services.syllabus_seed import ALL_CURRICULA

settings = get_settings()
router = APIRouter(prefix="/api/syllabus", tags=["syllabus"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/curricula")
async def list_curricula():
    """Return all supported curricula / boards."""
    return {"curricula": ALL_CURRICULA}


@router.get("/subjects", response_model=list[SubjectResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_subjects(
    request: Request,
    curriculum: str = Query(...),
    class_grade: int = Query(..., ge=6, le=12),
    stream: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Return subjects for a given curriculum, class, and optional stream."""
    stmt = (
        select(Subject)
        .where(Subject.curriculum == curriculum)
        .where(Subject.class_grade == class_grade)
    )
    if stream:
        stmt = stmt.where(Subject.stream == stream)
    else:
        stmt = stmt.where(Subject.stream.is_(None))

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/chapters/{subject_id}", response_model=list[ChapterResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_chapters(
    subject_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return chapters for a subject, ordered by chapter order."""
    subject = await db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    stmt = (
        select(Chapter)
        .where(Chapter.subject_id == subject_id)
        .order_by(Chapter.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/lessons/{chapter_id}", response_model=list[GeneratedLessonResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_generated_lessons(
    chapter_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return pre-generated lessons for a chapter."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    stmt = (
        select(GeneratedLesson)
        .where(GeneratedLesson.chapter_id == chapter_id)
        .order_by(GeneratedLesson.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/generate/{chapter_id}", response_model=GeneratedLessonResponse)
@limiter.limit(settings.RATE_LIMIT_ASK)
async def generate_chapter_lesson(
    chapter_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Use the AI pipeline to generate a detailed lesson for a chapter
    and persist it in the database.
    """
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Load subject for context
    subject = await db.get(Subject, chapter.subject_id)

    from app.services import rag_pipeline
    lang = user.language_preference or "en"

    prompt = (
        f"Create a comprehensive, detailed educational lesson on the topic: '{chapter.title}' "
        f"from the subject '{subject.name}' for class {subject.class_grade}. "
        f"You MUST include ALL of the following:\n"
        f"1. Key concepts explained in depth\n"
        f"2. ALL important formulas with explanation of each symbol\n"
        f"3. At least 2-3 fully worked-out example problems with step-by-step solutions\n"
        f"4. Common mistakes students make\n"
        f"5. At least 5 practice questions with answers\n"
        f"6. A real-world analogy to make the concept relatable\n"
        f"7. A quick summary of the most important points"
    )

    try:
        result = await rag_pipeline.generate_lesson(
            question=prompt,
            target_language=lang,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Count existing lessons for ordering
    count_stmt = select(GeneratedLesson).where(
        GeneratedLesson.chapter_id == chapter_id
    )
    existing = (await db.execute(count_stmt)).scalars().all()

    lesson = GeneratedLesson(
        chapter_id=chapter_id,
        title=chapter.title,
        content_markdown=result["content"],
        language_code=lang,
        order=len(existing) + 1,
    )
    db.add(lesson)
    await db.flush()
    await db.refresh(lesson)
    return lesson
