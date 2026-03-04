"""
Progress tracking API routes.

Endpoints:
  GET   /api/progress              → all progress records for current user
  GET   /api/progress/stats        → per-subject aggregated stats
  GET   /api/progress/{chapter_id} → progress for a specific chapter
  PATCH /api/progress/{chapter_id} → update progress for a chapter
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select, func, Integer as SAInteger
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Chapter, Subject, User, UserProgress
from app.schemas import SubjectStatsResponse, UserProgressResponse, UserProgressUpdate

settings = get_settings()
router = APIRouter(prefix="/api/progress", tags=["progress"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/stats", response_model=list[SubjectStatsResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_subject_stats(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return per-subject aggregated stats for the current user."""
    # Get all subjects for this user's curriculum/class
    subj_stmt = select(Subject).where(
        Subject.curriculum == (user.curriculum or "CBSE"),
        Subject.class_grade == (user.class_grade or 10),
    )
    if user.stream:
        subj_stmt = subj_stmt.where(
            (Subject.stream == user.stream) | (Subject.stream.is_(None))
        )
    subjects = (await db.execute(subj_stmt)).scalars().all()

    stats = []
    for subj in subjects:
        # Get all chapter IDs for this subject
        ch_stmt = select(Chapter.id).where(Chapter.subject_id == subj.id)
        chapter_ids = (await db.execute(ch_stmt)).scalars().all()
        total_chapters = len(chapter_ids)

        if not chapter_ids:
            stats.append(SubjectStatsResponse(
                subject_id=subj.id,
                subject_name=subj.name,
                total_chapters=total_chapters,
            ))
            continue

        # Aggregate progress for those chapters
        prog_stmt = (
            select(
                func.avg(UserProgress.quiz_score),
                func.sum(UserProgress.flashcards_reviewed),
                func.sum(UserProgress.time_spent_seconds),
                func.sum(func.cast(UserProgress.completed, SAInteger)),
            )
            .where(
                UserProgress.user_id == user.id,
                UserProgress.chapter_id.in_(chapter_ids),
            )
        )
        result = (await db.execute(prog_stmt)).one_or_none()
        avg_score, total_fc, total_time, completed = result or (None, 0, 0, 0)

        stats.append(SubjectStatsResponse(
            subject_id=subj.id,
            subject_name=subj.name,
            avg_quiz_score=round(avg_score, 1) if avg_score is not None else None,
            total_flashcards_reviewed=int(total_fc or 0),
            total_time_spent_seconds=int(total_time or 0),
            chapters_completed=int(completed or 0),
            total_chapters=total_chapters,
        ))

    return stats


@router.get("/", response_model=list[UserProgressResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_progress(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all progress records for the current user."""
    stmt = select(UserProgress).where(UserProgress.user_id == user.id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{chapter_id}", response_model=UserProgressResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_chapter_progress(
    chapter_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return progress for a specific chapter (creates if not exists)."""
    stmt = (
        select(UserProgress)
        .where(UserProgress.user_id == user.id)
        .where(UserProgress.chapter_id == chapter_id)
    )
    progress = (await db.execute(stmt)).scalar_one_or_none()

    if not progress:
        # Verify chapter exists
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")

        progress = UserProgress(user_id=user.id, chapter_id=chapter_id)
        db.add(progress)
        await db.flush()
        await db.refresh(progress)

    return progress


@router.patch("/{chapter_id}", response_model=UserProgressResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_chapter_progress(
    chapter_id: str,
    request: Request,
    body: UserProgressUpdate = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update progress fields for a chapter."""
    stmt = (
        select(UserProgress)
        .where(UserProgress.user_id == user.id)
        .where(UserProgress.chapter_id == chapter_id)
    )
    progress = (await db.execute(stmt)).scalar_one_or_none()

    if not progress:
        chapter = await db.get(Chapter, chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail="Chapter not found")
        progress = UserProgress(user_id=user.id, chapter_id=chapter_id)
        db.add(progress)

    if body.lessons_read is not None:
        progress.lessons_read = body.lessons_read
    if body.flashcards_reviewed is not None:
        progress.flashcards_reviewed = body.flashcards_reviewed
    if body.quiz_score is not None:
        progress.quiz_score = body.quiz_score
    if body.time_spent_seconds is not None:
        progress.time_spent_seconds = (progress.time_spent_seconds or 0) + body.time_spent_seconds
    if body.completed is not None:
        progress.completed = body.completed
    progress.updated_at = datetime.now(timezone.utc)

    await db.flush()
    await db.refresh(progress)
    return progress
