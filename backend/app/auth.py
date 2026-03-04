"""
Authentication helpers.

- Verify Auth0 ID tokens (Google Sign-In via Auth0).
- Issue / verify local JWT access tokens.
- FastAPI dependency to extract the current user from the Authorization header.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt, jwk
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models import User

logger = logging.getLogger(__name__)
settings = get_settings()

_bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Auth0 ID-token verification via JWKS
# ---------------------------------------------------------------------------

_jwks_cache: dict | None = None
_jwks_fetched_at: datetime | None = None
_JWKS_CACHE_TTL = timedelta(hours=6)


async def _get_auth0_jwks() -> dict:
    """Fetch and cache Auth0 JWKS (public signing keys)."""
    global _jwks_cache, _jwks_fetched_at

    now = datetime.now(timezone.utc)
    if _jwks_cache and _jwks_fetched_at and (now - _jwks_fetched_at) < _JWKS_CACHE_TTL:
        return _jwks_cache

    jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(jwks_url)
            resp.raise_for_status()
            _jwks_cache = resp.json()
            _jwks_fetched_at = now
            logger.info("Fetched Auth0 JWKS from %s", jwks_url)
            return _jwks_cache
    except Exception as exc:
        logger.error("Failed to fetch Auth0 JWKS: %s", exc)
        if _jwks_cache:
            logger.warning("Using stale JWKS cache.")
            return _jwks_cache
        raise HTTPException(status_code=503, detail="Auth service temporarily unavailable")


def _find_signing_key(jwks: dict, kid: str) -> dict:
    """Find the RSA key matching the token's kid in the JWKS."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return key
    raise HTTPException(status_code=401, detail="Invalid token signing key")


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


async def verify_auth0_token(id_token: str, request: Request | None = None) -> dict:
    """
    Verify an Auth0 ID token and return the decoded claims.

    In development (DEBUG=True), we allow unsigned tokens for local testing.
    In production (DEBUG=False), only RS256-signed Auth0 tokens are accepted.
    """
    # Determine client IP for logging
    client_ip = "unknown"
    if request and request.client:
        client_ip = request.client.host

    # Try to get the token header to check for RS256
    try:
        unverified_header = jwt.get_unverified_header(id_token)
    except JWTError:
        if settings.DEBUG:
            logger.info("Dev-mode token decode for IP %s", client_ip)
            return _decode_dev_token(id_token)
        logger.warning("Invalid token header from IP %s", client_ip)
        raise HTTPException(status_code=401, detail="Invalid token")

    alg = unverified_header.get("alg", "")

    # If it's an RS256 token (Auth0-signed), verify with JWKS
    if alg == "RS256":
        kid = unverified_header.get("kid")
        if not kid:
            raise HTTPException(status_code=401, detail="Token missing kid header")

        jwks = await _get_auth0_jwks()
        signing_key = _find_signing_key(jwks, kid)

        # Build the RSA public key
        rsa_key = {
            "kty": signing_key["kty"],
            "kid": signing_key["kid"],
            "use": signing_key.get("use", "sig"),
            "n": signing_key["n"],
            "e": signing_key["e"],
        }

        try:
            payload = jwt.decode(
                id_token,
                rsa_key,
                algorithms=["RS256"],
                audience=settings.AUTH0_CLIENT_ID,
                issuer=f"https://{settings.AUTH0_DOMAIN}/",
            )
            return payload
        except JWTError as exc:
            logger.warning("Auth0 token verification failed from IP %s: %s", client_ip, exc)
            raise HTTPException(status_code=401, detail="Invalid or expired token")

    # Non-RS256 token — only allow in dev mode
    if settings.DEBUG:
        logger.info("Dev-mode token decode (alg=%s) for IP %s", alg, client_ip)
        return _decode_dev_token(id_token)

    logger.warning("Rejecting non-RS256 token (alg=%s) from IP %s", alg, client_ip)
    raise HTTPException(status_code=401, detail="Unsupported token algorithm")


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
