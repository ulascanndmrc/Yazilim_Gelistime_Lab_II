"""
GREEN PHASE: Auth middleware implementation satisfying TDD tests.
Implements JWT validation, public route detection, and role checks.
"""
from typing import Optional
import jwt as pyjwt
from app.config import settings


# ─── Custom Exception Hierarchy ───────────────────────────────────────────────

class AuthError(Exception):
    status_code: int = 401
    detail: str = "Authentication failed"


class MissingTokenError(AuthError):
    detail = "Authorization token is missing"


class TokenExpiredError(AuthError):
    detail = "Token has expired"


class InvalidTokenError(AuthError):
    detail = "Invalid or malformed token"


class InsufficientPermissionsError(AuthError):
    status_code = 403
    detail = "Insufficient permissions"


# ─── Public Routes ────────────────────────────────────────────────────────────

_PUBLIC_ROUTES = [
    ("POST", "/auth/login"),
    ("POST", "/auth/register"),
    ("GET",  "/health"),
    ("GET",  "/metrics"),
    ("GET",  "/dashboard"),
    ("GET",  "/static"),
    ("GET",  "/api/gateway"),
]


def is_public_route(method: str, path: str) -> bool:
    """Return True if the route does not require JWT authentication."""
    for pub_method, pub_prefix in _PUBLIC_ROUTES:
        if method.upper() == pub_method and path.startswith(pub_prefix):
            return True
    if path.startswith("/static/"):
        return True
    return False


# ─── Token Utilities ──────────────────────────────────────────────────────────

def validate_token(token: Optional[str], secret: str) -> dict:
    """
    Decode and validate a JWT token.

    Raises:
        MissingTokenError   – token is None or empty
        TokenExpiredError   – token has expired
        InvalidTokenError   – signature/format invalid
    """
    if not token:
        raise MissingTokenError()
    try:
        payload = pyjwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
        return payload
    except pyjwt.ExpiredSignatureError:
        raise TokenExpiredError()
    except pyjwt.InvalidTokenError:
        raise InvalidTokenError()


def extract_token_from_header(authorization: Optional[str]) -> Optional[str]:
    """Extract the raw token from a 'Bearer <token>' Authorization header."""
    if not authorization:
        return None
    parts = authorization.strip().split(" ")
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


def has_required_role(payload: dict, required_role: str) -> bool:
    """Check if the JWT payload satisfies the minimum role level."""
    hierarchy = {"admin": 2, "user": 1, "guest": 0}
    user_level = hierarchy.get(payload.get("role", "guest"), 0)
    required_level = hierarchy.get(required_role, 0)
    return user_level >= required_level
