"""
Authentication API routes.

Endpoints:
  POST /api/auth/google     → Google Sign-In (Firebase ID token → JWT)
  POST /api/auth/onboarding → Complete curriculum onboarding
  GET  /api/auth/me         → Get current user profile
  PATCH /api/auth/profile   → Update profile fields
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, verify_firebase_token
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import (
    AuthResponse,
    GoogleAuthRequest,
    OnboardingRequest,
    ProfileUpdateRequest,
    UpdateLanguageRequest,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


# ──────────────────────────────────────────────
#  POST /api/auth/google
# ──────────────────────────────────────────────

@router.post("/google", response_model=AuthResponse)
@limiter.limit("20/minute")
async def google_sign_in(
    request: Request,
    body: GoogleAuthRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Accept a Firebase ID token from the client, verify it,
    create-or-update the user, and return a local JWT.
    """
    claims = await verify_firebase_token(body.id_token, request=request)

    firebase_uid = claims.get("uid") or claims.get("sub") or claims.get("user_id")
    email = claims.get("email", "")
    name = claims.get("name", email.split("@")[0] if email else "Student")
    picture = claims.get("picture")

    if not firebase_uid:
        raise HTTPException(status_code=400, detail="Token missing uid")

    # Look up by firebase_uid first, then by email as fallback
    stmt = select(User).where(User.firebase_uid == firebase_uid)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        # Check if an email-only user exists (legacy)
        stmt2 = select(User).where(User.email == email)
        user = (await db.execute(stmt2)).scalar_one_or_none()
        if user:
            user.firebase_uid = firebase_uid
            if picture:
                user.profile_picture_url = picture
        else:
            user = User(
                firebase_uid=firebase_uid,
                name=name,
                email=email,
                profile_picture_url=picture,
            )
            db.add(user)
    else:
        # Update profile fields on each login
        if name:
            user.name = name
        if picture:
            user.profile_picture_url = picture

    await db.flush()
    await db.refresh(user)

    token = create_access_token(user.id, user.email)
    return AuthResponse(access_token=token, user=UserResponse.model_validate(user))


# ──────────────────────────────────────────────
#  POST /api/auth/onboarding
# ──────────────────────────────────────────────

@router.post("/onboarding", response_model=UserResponse)
@limiter.limit("10/minute")
async def complete_onboarding(
    request: Request,
    body: OnboardingRequest = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Student selects their curriculum, class, stream, and language."""
    user.curriculum = body.curriculum
    user.class_grade = body.class_grade
    user.stream = body.stream
    user.language_preference = body.language_preference
    user.onboarding_complete = True
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)


# ──────────────────────────────────────────────
#  GET /api/auth/me
# ──────────────────────────────────────────────

@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return UserResponse.model_validate(user)


# ──────────────────────────────────────────────
#  PATCH /api/auth/profile
# ──────────────────────────────────────────────

@router.patch("/profile", response_model=UserResponse)
@limiter.limit("10/minute")
async def update_profile(
    request: Request,
    body: ProfileUpdateRequest = Body(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update curriculum/class/stream/language after onboarding (partial)."""
    if body.curriculum is not None:
        user.curriculum = body.curriculum
    if body.class_grade is not None:
        user.class_grade = body.class_grade
    if body.stream is not None:
        user.stream = body.stream
    if body.language_preference is not None:
        user.language_preference = body.language_preference
    await db.flush()
    await db.refresh(user)
    return UserResponse.model_validate(user)
