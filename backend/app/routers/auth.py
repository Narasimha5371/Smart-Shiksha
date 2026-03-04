"""
Authentication API routes.

Endpoints:
  POST /api/auth/login      → Auth0 ID token → local JWT
  POST /api/auth/google     → Backward-compat alias for /login
  POST /api/auth/onboarding → Complete curriculum onboarding
  GET  /api/auth/me         → Get current user profile
  PATCH /api/auth/profile   → Update profile fields
"""

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_access_token, get_current_user, verify_auth0_token
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import (
    AuthResponse,
    AuthTokenRequest,
    OnboardingRequest,
    ProfileUpdateRequest,
    UpdateLanguageRequest,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


# ──────────────────────────────────────────────
#  POST /api/auth/login
# ──────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
async def auth0_login(
    request: Request,
    body: AuthTokenRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """
    Accept an Auth0 ID token from the client, verify it,
    create-or-update the user, and return a local JWT.
    """
    claims = await verify_auth0_token(body.id_token, request=request)

    # Auth0 sub format: "google-oauth2|123456" or "auth0|abc123"
    auth0_sub = claims.get("sub", "")
    email = claims.get("email", "")
    name = claims.get("name") or claims.get("nickname") or (email.split("@")[0] if email else "Student")
    picture = claims.get("picture")

    if not auth0_sub:
        raise HTTPException(status_code=400, detail="Token missing sub claim")

    # Look up by firebase_uid (reusing the column for Auth0 sub)
    stmt = select(User).where(User.firebase_uid == auth0_sub)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        # Check if an email-only user exists (legacy)
        if email:
            stmt2 = select(User).where(User.email == email)
            user = (await db.execute(stmt2)).scalar_one_or_none()
        if user:
            user.firebase_uid = auth0_sub
            if picture:
                user.profile_picture_url = picture
        else:
            user = User(
                firebase_uid=auth0_sub,
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


# Backward-compatible alias so Flutter client (/api/auth/google) still works
@router.post("/google", response_model=AuthResponse, include_in_schema=False)
@limiter.limit("20/minute")
async def google_sign_in_compat(
    request: Request,
    body: AuthTokenRequest = Body(...),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    return await auth0_login(request=request, body=body, db=db)


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
