"""
Quiz / Flashcard API routes.

Endpoints:
  GET  /api/quiz/flashcards/{chapter_id}   → get flashcards for a chapter
  POST /api/quiz/generate/{chapter_id}     → AI-generate flashcards for a chapter
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import Chapter, FlashCard, Subject, User
from app.schemas import FlashCardResponse

logger = logging.getLogger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/quiz", tags=["quiz"])
limiter = Limiter(key_func=get_remote_address)


@router.get("/flashcards/{chapter_id}", response_model=list[FlashCardResponse])
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def list_flashcards(
    chapter_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Return flashcards for a chapter, ordered."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    stmt = (
        select(FlashCard)
        .where(FlashCard.chapter_id == chapter_id)
        .order_by(FlashCard.order)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/generate/{chapter_id}", response_model=list[FlashCardResponse])
@limiter.limit(settings.RATE_LIMIT_ASK)
async def generate_flashcards(
    chapter_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    AI-generate quiz questions (MCQ, MSQ, Numerical) for a chapter.
    Skips if questions already exist.
    """
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    # Check existing
    existing_stmt = select(FlashCard).where(FlashCard.chapter_id == chapter_id)
    existing = (await db.execute(existing_stmt)).scalars().all()
    if existing:
        return existing

    subject = await db.get(Subject, chapter.subject_id)
    lang = user.language_preference or "en"

    from app.services.groq_service import call_groq
    from app.config import SUPPORTED_LANGUAGES
    lang_name = SUPPORTED_LANGUAGES.get(lang, "English")

    prompt = (
        f"Generate a quiz for the chapter '{chapter.title}' "
        f"from '{subject.name}' (class {subject.class_grade}).\n\n"
        f"Create exactly 15 questions with this distribution:\n"
        f"  - 7 MCQ (Multiple Choice Questions) with exactly ONE correct answer\n"
        f"  - 4 MSQ (Multiple Select Questions) with TWO or MORE correct answers\n"
        f"  - 4 Numerical (the answer is a single number)\n\n"
        f"Write ALL question text and options in {lang_name} language.\n\n"
        f"Return a JSON array. Each object must have these fields:\n"
        f'  "type": "mcq" | "msq" | "numerical"\n'
        f'  "question": the question text\n'
        f'  "options": ["A. ...", "B. ...", "C. ...", "D. ..."]  (omit for numerical)\n'
        f'  "answer": correct option letter(s) — single letter for MCQ (e.g. "B"), '
        f'comma-separated for MSQ (e.g. "A,C"), or a number string for numerical (e.g. "42")\n'
        f'  "explanation": a brief 1-2 sentence explanation of the correct answer\n\n'
        f"Example:\n"
        f'[{{"type":"mcq","question":"What is 2+2?","options":["A. 3","B. 4","C. 5","D. 6"],"answer":"B","explanation":"2+2 equals 4."}},'
        f'{{"type":"msq","question":"Which are prime?","options":["A. 2","B. 4","C. 5","D. 9"],"answer":"A,C","explanation":"2 and 5 are prime."}},'
        f'{{"type":"numerical","question":"Solve: 6 × 7 = ?","answer":"42","explanation":"6 times 7 is 42."}}]\n\n'
        f"Return ONLY the JSON array, no extra text."
    )

    try:
        raw = await call_groq(prompt, language=lang)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Parse JSON from response
    cards = []
    try:
        text = raw.strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            cards = json.loads(text[start:end])
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Failed to parse quiz JSON: %s", e)
        cards = [{"type": "mcq", "question": f"Review: {chapter.title}",
                  "options": ["A. See lesson"], "answer": "A",
                  "explanation": raw[:500]}]

    created = []
    for idx, card in enumerate(cards[:15], 1):
        q_type = card.get("type", "mcq")
        if q_type not in ("mcq", "msq", "numerical"):
            q_type = "mcq"

        fc = FlashCard(
            chapter_id=chapter_id,
            question=card.get("question", f"Q{idx}"),
            answer=card.get("answer", ""),
            question_type=q_type,
            options_json=card.get("options") if q_type in ("mcq", "msq") else None,
            explanation=card.get("explanation"),
            order=idx,
        )
        db.add(fc)
        created.append(fc)

    await db.flush()
    for fc in created:
        await db.refresh(fc)
    return created
