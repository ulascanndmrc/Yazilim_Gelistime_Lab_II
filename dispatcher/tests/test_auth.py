"""
TDD - RED PHASE: Auth/JWT validation tests for the Dispatcher.
Written BEFORE implementation (Red-Green-Refactor cycle).
File created: dispatcher/tests/test_auth.py  <-- BEFORE dispatcher/app/auth_middleware.py
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

JWT_SECRET = "test-secret-key"
ALGORITHM = "HS256"


def _make_token(payload: dict, secret: str = JWT_SECRET, expired: bool = False) -> str:
    import jwt
    data = payload.copy()
    exp = datetime.utcnow() + (timedelta(seconds=-10) if expired else timedelta(hours=1))
    data["exp"] = exp
    return jwt.encode(data, secret, algorithm=ALGORITHM)


class TestJWTValidation:

    def test_valid_token_returns_payload(self):
        from app.auth_middleware import validate_token
        token = _make_token({"sub": "user123", "role": "user"})
        payload = validate_token(token, JWT_SECRET)
        assert payload["sub"] == "user123"
        assert payload["role"] == "user"

    def test_expired_token_raises_TokenExpiredError(self):
        from app.auth_middleware import validate_token, TokenExpiredError
        token = _make_token({"sub": "user123"}, expired=True)
        with pytest.raises(TokenExpiredError):
            validate_token(token, JWT_SECRET)

    def test_wrong_secret_raises_InvalidTokenError(self):
        from app.auth_middleware import validate_token, InvalidTokenError
        token = _make_token({"sub": "user123"}, secret="wrong-secret")
        with pytest.raises(InvalidTokenError):
            validate_token(token, JWT_SECRET)

    def test_none_token_raises_MissingTokenError(self):
        from app.auth_middleware import validate_token, MissingTokenError
        with pytest.raises(MissingTokenError):
            validate_token(None, JWT_SECRET)

    def test_empty_token_raises_MissingTokenError(self):
        from app.auth_middleware import validate_token, MissingTokenError
        with pytest.raises(MissingTokenError):
            validate_token("", JWT_SECRET)


class TestPublicRoutes:

    def test_login_is_public(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("POST", "/auth/login") is True

    def test_register_is_public(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("POST", "/auth/register") is True

    def test_health_is_public(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("GET", "/health") is True

    def test_dashboard_is_public(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("GET", "/dashboard") is True

    def test_api_messages_is_protected(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("GET", "/api/messages") is False

    def test_api_users_is_protected(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("GET", "/api/users") is False

    def test_api_products_is_protected(self):
        from app.auth_middleware import is_public_route
        assert is_public_route("DELETE", "/api/products/1") is False


class TestRoleAuthorization:

    def test_admin_passes_admin_check(self):
        from app.auth_middleware import has_required_role
        assert has_required_role({"role": "admin"}, "admin") is True

    def test_user_fails_admin_check(self):
        from app.auth_middleware import has_required_role
        assert has_required_role({"role": "user"}, "admin") is False

    def test_admin_passes_user_check(self):
        from app.auth_middleware import has_required_role
        assert has_required_role({"role": "admin"}, "user") is True

    def test_user_passes_user_check(self):
        from app.auth_middleware import has_required_role
        assert has_required_role({"role": "user"}, "user") is True


class TestTokenExtraction:

    def test_extracts_bearer_token(self):
        from app.auth_middleware import extract_token_from_header
        token = extract_token_from_header("Bearer mytoken123")
        assert token == "mytoken123"

    def test_missing_header_returns_none(self):
        from app.auth_middleware import extract_token_from_header
        assert extract_token_from_header(None) is None

    def test_malformed_header_returns_none(self):
        from app.auth_middleware import extract_token_from_header
        assert extract_token_from_header("NotBearer token") is None
