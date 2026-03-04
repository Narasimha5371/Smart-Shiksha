"""
SQLAlchemy ORM models.

Tables:
  - users              → student accounts with curriculum/class/stream
  - saved_lessons      → cached AI-generated lessons per user
  - subjects           → subjects per curriculum/class
  - chapters           → chapters within a subject
  - generated_lessons  → pre-generated AI lesson content
  - flashcards         → flashcard Q&A per chapter
  - user_progress      → per-chapter progress tracking
  - competitive_exams  → JEE / NEET exam metadata
  - mock_tests         → generated mock test papers
  - mock_test_attempts → student attempt records

UUID primary keys for distributed-system readiness.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, DateTime, Float, ForeignKey, Integer, String, Text, JSON,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    """Shared declarative base for all models."""
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    firebase_uid: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    profile_picture_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
    )
    language_preference: Mapped[str] = mapped_column(
        String(5), nullable=False, default="en",
    )

    # Curriculum / onboarding fields
    curriculum: Mapped[str | None] = mapped_column(String(30), nullable=True)
    class_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stream: Mapped[str | None] = mapped_column(String(30), nullable=True)
    onboarding_complete: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    saved_lessons: Mapped[list[SavedLesson]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    progress: Mapped[list[UserProgress]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )
    mock_test_attempts: Mapped[list[MockTestAttempt]] = relationship(
        back_populates="user", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.name!r} ({self.language_preference})>"


class SavedLesson(Base):
    __tablename__ = "saved_lessons"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language_code: Mapped[str] = mapped_column(String(5), nullable=False)
    source_urls: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped[User] = relationship(back_populates="saved_lessons")

    def __repr__(self) -> str:
        return f"<SavedLesson {self.topic!r} [{self.language_code}]>"


# ──────────────────────────────────────────────
#  Syllabus / Curriculum Models
# ──────────────────────────────────────────────

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    curriculum: Mapped[str] = mapped_column(String(30), nullable=False)
    class_grade: Mapped[int] = mapped_column(Integer, nullable=False)
    stream: Mapped[str | None] = mapped_column(String(30), nullable=True)
    icon_name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="subject", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Subject {self.name!r} ({self.curriculum} {self.class_grade})>"


class Chapter(Base):
    __tablename__ = "chapters"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    subject_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject: Mapped[Subject] = relationship(back_populates="chapters")
    generated_lessons: Mapped[list[GeneratedLesson]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan",
    )
    flashcards: Mapped[list[FlashCard]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan",
    )
    user_progress: Mapped[list[UserProgress]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Chapter {self.title!r}>"


class GeneratedLesson(Base):
    __tablename__ = "generated_lessons"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_markdown: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    language_code: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    chapter: Mapped[Chapter] = relationship(back_populates="generated_lessons")

    def __repr__(self) -> str:
        return f"<GeneratedLesson {self.title!r}>"


class FlashCard(Base):
    __tablename__ = "flashcards"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    # "mcq" | "msq" | "numerical"
    question_type: Mapped[str] = mapped_column(
        String(16), nullable=False, default="mcq",
    )
    # JSON list of option strings for MCQ/MSQ, e.g. ["A. ...", "B. ..."]
    options_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # For MSQ: comma-separated correct keys like "A,C"; for numerical: the numeric answer
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    chapter: Mapped[Chapter] = relationship(back_populates="flashcards")

    def __repr__(self) -> str:
        return f"<FlashCard({self.question_type}) Q={self.question[:40]!r}>"


class UserProgress(Base):
    __tablename__ = "user_progress"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False,
    )
    lessons_read: Mapped[int] = mapped_column(Integer, default=0)
    flashcards_reviewed: Mapped[int] = mapped_column(Integer, default=0)
    quiz_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_spent_seconds: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[User] = relationship(back_populates="progress")
    chapter: Mapped[Chapter] = relationship(back_populates="user_progress")


# ──────────────────────────────────────────────
#  Competitive Exam Models
# ──────────────────────────────────────────────

class CompetitiveExam(Base):
    __tablename__ = "competitive_exams"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    subjects_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # Class range this exam targets (inclusive)
    class_min: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    class_max: Mapped[int] = mapped_column(Integer, nullable=False, default=12)

    mock_tests: Mapped[list[MockTest]] = relationship(
        back_populates="exam", cascade="all, delete-orphan",
    )


class MockTest(Base):
    __tablename__ = "mock_tests"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    exam_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("competitive_exams.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    questions_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=180)
    total_marks: Mapped[int] = mapped_column(Integer, default=360)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    exam: Mapped[CompetitiveExam] = relationship(back_populates="mock_tests")
    attempts: Mapped[list[MockTestAttempt]] = relationship(
        back_populates="mock_test", cascade="all, delete-orphan",
    )


class MockTestAttempt(Base):
    __tablename__ = "mock_test_attempts"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4()),
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    mock_test_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("mock_tests.id", ondelete="CASCADE"), nullable=False,
    )
    answers_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_taken_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped[User] = relationship(back_populates="mock_test_attempts")
    mock_test: Mapped[MockTest] = relationship(back_populates="attempts")
