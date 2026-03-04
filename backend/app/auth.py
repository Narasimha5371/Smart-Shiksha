"""
Authentication helpers.

- Verify Firebase ID tokens (Google Sign-In).
- Issue / verify local JWT access tokens.
- FastAPI dependency to extract the current user from the Authorization header.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

_bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Firebase ID-token verification (lightweight — no firebase-admin dependency
# at import time so the rest of the app works even if firebase isn't set up).
# ---------------------------------------------------------------------------

_firebase_app = None
_firebase_works = None  # True/False/None(untested)


def _get_firebase_app():
    """Lazy-init Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None:
        try:
            import firebase_admin  # type: ignore
            from firebase_admin import credentials  # type: ignore

            # Use default credentials or project-id-only credential
            try:
                _firebase_app = firebase_admin.get_app()
            except ValueError:
                cred = credentials.ApplicationDefault()
                _firebase_app = firebase_admin.initialize_app(cred, {
                    "projectId": settings.FIREBASE_PROJECT_ID,
                })
        except Exception:
            if settings.DEBUG:
                # Firebase not configured — fall back in dev mode only
                logger.warning("Firebase Admin SDK not configured; using UNSAFE token decode (DEBUG=True).")
                _firebase_app = "DUMMY"
            else:
                logger.error(
                    "Firebase Admin SDK not configured and DEBUG=False. "
                    "Authentication will reject all Firebase tokens."
                )
                _firebase_app = "REJECTED"
    return _firebase_app


def _decode_dev_token(id_token: str) -> dict:
    """Decode a base64 JSON or unsigned JWT token for dev mode.
    Only callable when settings.DEBUG is True."""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=401,
            detail="Dev-mode token decode is disabled in production",
        )

    import base64, json as _json

    # Try plain base64 JSON first (Flutter dev client)
    try:
        decoded_bytes = base64.b64decode(id_token + "==")  # pad if needed
        payload = _json.loads(decoded_bytes)
        if isinstance(payload, dict):
            return payload
    except Exception:
        pass

    # Try as an unsigned JWT
    try:
        payload = jwt.get_unverified_claims(id_token)
        return payload
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


async def verify_firebase_token(id_token: str, request: Request | None = None) -> dict:
    """
    Verify a Firebase ID token and return the decoded claims.

    In development (DEBUG=True, no Firebase credentials), we decode without
    verification so Google Sign-In still works for local testing.
    In production (DEBUG=False), unsigned tokens are always rejected.
    """
    global _firebase_works
    app = _get_firebase_app()

    # Determine client IP for logging
    client_ip = "unknown"
    if request and request.client:
        client_ip = request.client.host

    if app == "REJECTED":
        logger.warning("Auth rejected (no Firebase, production mode) from IP %s", client_ip)
        raise HTTPException(
            status_code=401,
            detail="Authentication service unavailable",
        )

    if app == "DUMMY":
        logger.info("Dev-mode token decode for IP %s", client_ip)
        return _decode_dev_token(id_token)

    # Firebase SDK is loaded — try real verification
    if _firebase_works is not False:
        try:
            from firebase_admin import auth as fb_auth  # type: ignore
            decoded = fb_auth.verify_id_token(id_token, app=app)
            _firebase_works = True
            return decoded
        except Exception as exc:
            error_msg = str(exc)
            # If credentials aren't set up, fall back to dev mode only if DEBUG
            if "credentials" in error_msg.lower() or "default credentials" in error_msg.lower():
                if settings.DEBUG:
                    logger.warning("Firebase credentials not found; switching to dev mode (DEBUG=True).")
                    _firebase_works = False
                    return _decode_dev_token(id_token)
                else:
                    logger.error("Firebase credentials not configured in production. Rejecting token from IP %s.", client_ip)
                    raise HTTPException(status_code=401, detail="Authentication service unavailable")
            logger.warning("Firebase token verification failed from IP %s: %s", client_ip, exc)
            raise HTTPException(status_code=401, detail="Invalid Firebase token")

    # _firebase_works is False — use dev fallback (only works if DEBUG=True)
    if settings.DEBUG:
        return _decode_dev_token(id_token)

    logger.warning("Rejecting token (no Firebase, production mode) from IP %s", client_ip)
    raise HTTPException(status_code=401, detail="Authentication service unavailable")


# ---------------------------------------------------------------------------
# Local JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, email: str) -> str:
    """Create a signed JWT for internal API usage."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        logger.warning("JWT decode failed for a token attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalid or expired",
        )


# ---------------------------------------------------------------------------
# FastAPI dependency: Get current user
# ---------------------------------------------------------------------------

async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the Bearer JWT, then return the User ORM object.
    Used as a dependency in protected endpoints.
    """
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    payload = _decode_access_token(creds.credentials)
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
