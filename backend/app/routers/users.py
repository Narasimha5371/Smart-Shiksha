"""
User-related API routes.

Endpoints:
  POST  /api/users/register             → Create a new student account
  PATCH /api/users/{user_id}/language    → Update language preference (auth + ownership)
  GET   /api/users/{user_id}            → Get user profile (auth + ownership)
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import (
    UpdateLanguageRequest,
    UserCreate,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/api/users", tags=["users"])

limiter = Limiter(key_func=get_remote_address)


# ──────────────────────────────────────────────
#  POST /api/users/register
# ──────────────────────────────────────────────

@router.post("/register", response_model=UserResponse, status_code=201)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def register_user(
    request: Request,
    body: UserCreate = Body(...),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new student with an optional language preference."""
    # Check for duplicate email
    stmt = select(User).where(User.email == body.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        name=body.name,
        email=body.email,
        language_preference=body.language_preference,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ──────────────────────────────────────────────
#  GET /api/users/{user_id}  (auth + ownership)
# ──────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def get_user(
    user_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Retrieve a user profile by ID. Users can only access their own profile."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return current_user


# ──────────────────────────────────────────────
#  PATCH /api/users/{user_id}/language  (auth + ownership)
# ──────────────────────────────────────────────

@router.patch("/{user_id}/language", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def update_language(
    user_id: str,
    request: Request,
    body: UpdateLanguageRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the student's preferred language. Users can only update their own."""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")

    current_user.language_preference = body.language_preference
    await db.flush()
    await db.refresh(current_user)
    return current_user
