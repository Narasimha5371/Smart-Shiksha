"""
Competitive Exam / Mock Test API routes.

Endpoints:
  GET  /api/exams                         → list exams (JEE, NEET)
  GET  /api/exams/{exam_id}/mock-tests    → list mock tests for an exam
  GET  /api/exams/mock-tests/{test_id}    → get a full mock test with questions
  POST /api/exams/mock-tests/{test_id}/generate → AI-generate a mock test
  POST /api/exams/mock-tests/{test_id}/attempt  → submit an attempt
  GET  /api/exams/attempts                → list user's attempts
"""

import json
import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import CompetitiveExam, MockTest, MockTestAttempt, User
from app.schemas import (
    CompetitiveExamResponse,
    MockTestAttemptCreate,
    MockTestAttemptResponse,
    MockTestResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/exams", tags=["competitive-exams"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/", response_model=list[CompetitiveExamResponse])
async def list_exams(
    class_grade: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return competitive exams, optionally filtered by class grade."""
    stmt = select(CompetitiveExam)
    if class_grade is not None:
        stmt = stmt.where(
            CompetitiveExam.class_min <= class_grade,
            CompetitiveExam.class_max >= class_grade,
        )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{exam_id}/mock-tests", response_model=list[MockTestResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_mock_tests(
    exam_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return mock tests for a given exam."""
    exam = await db.get(CompetitiveExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    stmt = (
        select(MockTest)
        .where(MockTest.exam_id == exam_id)
        .order_by(MockTest.created_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/mock-tests/{test_id}", response_model=MockTestResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_mock_test(
    test_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return a full mock test including questions."""
    test = await db.get(MockTest, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Mock test not found")
    return test


@router.post("/mock-tests/{exam_id}/generate", response_model=MockTestResponse)
@limiter.limit(settings.RATE_LIMIT_ASK)
async def generate_mock_test(
    exam_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-generate a new mock test with MCQ questions for the given exam.
    """
    exam = await db.get(CompetitiveExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    from app.services.groq_service import call_groq

    subjects = ", ".join(exam.subjects_json or [])
    lang = user.language_preference or "en"

    from app.config import SUPPORTED_LANGUAGES
    lang_name = SUPPORTED_LANGUAGES.get(lang, "English")

    prompt = (
        f"Generate a {exam.name} mock test with 30 multiple-choice questions "
        f"covering: {subjects}. For each question provide exactly 4 options "
        f"(A, B, C, D) and the correct answer key. "
        f"Write ALL question text and options in {lang_name} language. "
        f"Format as a JSON array: "
        f'[{{"q": "...", "options": {{"A":"...", "B":"...", "C":"...", "D":"..."}}, "answer": "A"}}] '
        f"\nReturn ONLY the JSON array."
    )

    try:
        raw = await call_groq(prompt, language=lang)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    questions = []
    try:
        text = raw.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            questions = json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse mock test JSON: %s", e)
        questions = [{"q": "Error generating questions. Please try again.", "options": {}, "answer": ""}]

    # Count existing tests
    count_stmt = select(MockTest).where(MockTest.exam_id == exam_id)
    existing = (await db.execute(count_stmt)).scalars().all()

    mock_test = MockTest(
        exam_id=exam_id,
        title=f"{exam.name} Mock Test #{len(existing) + 1}",
        questions_json=questions,
        duration_minutes=180 if "JEE" in exam.name else 200,
        total_marks=len(questions) * 4,
    )
    db.add(mock_test)
    await db.flush()
    await db.refresh(mock_test)
    return mock_test


@router.post("/mock-tests/{test_id}/attempt", response_model=MockTestAttemptResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def submit_attempt(
    test_id: str,
    request: Request,
    body: MockTestAttemptCreate = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit answers for a mock test and get auto-scored."""
    test = await db.get(MockTest, test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Mock test not found")

    # Auto-score
    score = 0.0
    questions = test.questions_json or []
    for q in questions:
        q_text = q.get("q", "")
        correct = q.get("answer", "")
        student_answer = body.answers_json.get(q_text, "")
        if student_answer.upper() == correct.upper():
            score += 4  # +4 for correct
        elif student_answer:
            score -= 1  # -1 for wrong (JEE/NEET style)

    attempt = MockTestAttempt(
        user_id=user.id,
        mock_test_id=test_id,
        answers_json=body.answers_json,
        score=score,
        time_taken_minutes=body.time_taken_minutes,
    )
    db.add(attempt)
    await db.flush()
    await db.refresh(attempt)
    return attempt


@router.get("/attempts", response_model=list[MockTestAttemptResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_attempts(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return all mock test attempts for the current user."""
    stmt = (
        select(MockTestAttempt)
        .where(MockTestAttempt.user_id == user.id)
        .order_by(MockTestAttempt.completed_at.desc())
    )
    result = await db.execute(stmt)
    return result.scalars().all()
