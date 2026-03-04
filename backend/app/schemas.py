"""
Pydantic schemas for request/response validation.

Every API payload is strictly validated here — no raw dicts pass through.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

# Re-export the canonical language code type
LanguageCode = Literal["en", "hi", "kn", "te", "ta"]


# ──────────────────────────────────────────────
#  Auth
# ──────────────────────────────────────────────

class GoogleAuthRequest(BaseModel):
    """Client sends the Firebase ID token after Google Sign-In."""
    id_token: str = Field(..., min_length=10)


class AuthResponse(BaseModel):
    """JWT + user profile returned after successful auth."""
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class OnboardingRequest(BaseModel):
    """Student completes onboarding by selecting curriculum details."""
    curriculum: str = Field(..., min_length=1, max_length=30)
    class_grade: int = Field(..., ge=6, le=12)
    stream: str | None = Field(
        default=None, max_length=30,
        description="Required for class 11-12 (science / commerce / arts)",
    )
    language_preference: LanguageCode = "en"


# ──────────────────────────────────────────────
#  Ask / RAG Pipeline
# ──────────────────────────────────────────────

class AskRequest(BaseModel):
    """Student submits a question with a target language."""
    question: str = Field(
        ..., min_length=3, max_length=1000,
        description="The student's academic question",
    )
    target_language: LanguageCode = Field(
        default="en",
        description="Language code for the AI-generated response",
    )


class AskResponse(BaseModel):
    """AI-generated lesson returned to the student."""
    topic: str
    content: str          # Markdown-formatted lesson
    language: str
    sources: list[str]    # URLs used as RAG context


# ──────────────────────────────────────────────
#  Saved Lessons
# ──────────────────────────────────────────────

class SaveLessonRequest(BaseModel):
    """Save a generated lesson for offline reading."""
    user_id: str
    topic: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    language_code: LanguageCode = "en"
    source_urls: list[str] = []


class LessonResponse(BaseModel):
    """A single saved lesson returned from the database."""
    id: str
    topic: str
    content: str
    language_code: str
    source_urls: list[str] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
#  Users
# ──────────────────────────────────────────────

class UserCreate(BaseModel):
    """Register a new student."""
    name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    language_preference: LanguageCode = "en"


class UserResponse(BaseModel):
    """Public user representation."""
    id: str
    name: str
    email: str
    profile_picture_url: str | None = None
    language_preference: str
    curriculum: str | None = None
    class_grade: int | None = None
    stream: str | None = None
    onboarding_complete: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateLanguageRequest(BaseModel):
    """Update a user's preferred language."""
    language_preference: LanguageCode


# ──────────────────────────────────────────────
#  Syllabus
# ──────────────────────────────────────────────

class SubjectResponse(BaseModel):
    id: str
    name: str
    curriculum: str
    class_grade: int
    stream: str | None = None
    icon_name: str | None = None
    model_config = {"from_attributes": True}


class ChapterResponse(BaseModel):
    id: str
    subject_id: str
    title: str
    order: int
    description: str | None = None
    model_config = {"from_attributes": True}


class GeneratedLessonResponse(BaseModel):
    id: str
    chapter_id: str
    title: str
    content_markdown: str
    image_url: str | None = None
    language_code: str
    order: int
    created_at: datetime
    model_config = {"from_attributes": True}


class FlashCardResponse(BaseModel):
    id: str
    chapter_id: str
    question: str
    answer: str
    question_type: str = "mcq"  # mcq | msq | numerical
    options_json: list | None = None
    explanation: str | None = None
    order: int
    model_config = {"from_attributes": True}


class UserProgressResponse(BaseModel):
    id: str
    user_id: str
    chapter_id: str
    lessons_read: int
    flashcards_reviewed: int
    quiz_score: float | None = None
    time_spent_seconds: int = 0
    completed: bool
    updated_at: datetime
    model_config = {"from_attributes": True}


class UserProgressUpdate(BaseModel):
    lessons_read: int | None = None
    flashcards_reviewed: int | None = None
    quiz_score: float | None = None
    time_spent_seconds: int | None = None
    completed: bool | None = None


class ProfileUpdateRequest(BaseModel):
    """Partial profile update — all fields optional."""
    curriculum: str | None = None
    class_grade: int | None = Field(default=None, ge=6, le=12)
    stream: str | None = None
    language_preference: LanguageCode | None = None


class SubjectStatsResponse(BaseModel):
    """Aggregated stats for a single subject."""
    subject_id: str
    subject_name: str
    avg_quiz_score: float | None = None
    total_flashcards_reviewed: int = 0
    total_time_spent_seconds: int = 0
    chapters_completed: int = 0
    total_chapters: int = 0


# ──────────────────────────────────────────────
#  Competitive Exams
# ──────────────────────────────────────────────

class CompetitiveExamResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    subjects_json: list | None = None
    class_min: int = 6
    class_max: int = 12
    model_config = {"from_attributes": True}


class MockTestResponse(BaseModel):
    id: str
    exam_id: str
    title: str
    questions_json: list | None = None
    duration_minutes: int
    total_marks: int
    created_at: datetime
    model_config = {"from_attributes": True}


class MockTestAttemptCreate(BaseModel):
    mock_test_id: str
    answers_json: dict
    time_taken_minutes: int | None = None


class MockTestAttemptResponse(BaseModel):
    id: str
    user_id: str
    mock_test_id: str
    answers_json: dict | None = None
    score: float | None = None
    time_taken_minutes: int | None = None
    completed_at: datetime
    model_config = {"from_attributes": True}


# Forward-ref resolution
AuthResponse.model_rebuild()
