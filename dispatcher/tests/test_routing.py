"""
TDD - RED PHASE: Routing tests for the Dispatcher API Gateway.
Written BEFORE implementation (Red-Green-Refactor cycle).
File created: dispatcher/tests/test_routing.py  <-- BEFORE dispatcher/app/router.py
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestServiceRouting:
    """Tests for URL-based routing to microservices."""

    def test_auth_login_routes_to_login_service(self):
        from app.router import get_service_url
        result = get_service_url("POST", "/auth/login")
        assert result is not None
        target_url, service = result
        assert service == "login-service"

    def test_auth_register_routes_to_login_service(self):
        from app.router import get_service_url
        result = get_service_url("POST", "/auth/register")
        assert result is not None
        _, service = result
        assert service == "login-service"

    def test_messages_routes_to_message_service(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/messages")
        assert result is not None
        _, service = result
        assert service == "message-service"

    def test_users_routes_to_user_service(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/users")
        assert result is not None
        _, service = result
        assert service == "user-service"

    def test_products_routes_to_product_service(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/products")
        assert result is not None
        _, service = result
        assert service == "product-service"

    def test_reports_routes_to_report_service(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/reports")
        assert result is not None
        _, service = result
        assert service == "report-service"

    def test_unknown_route_returns_none(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/unknown")
        assert result is None

    def test_nested_path_routes_correctly(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/messages/123")
        assert result is not None
        target_url, service = result
        assert service == "message-service"
        assert "/api/messages/123" in target_url

    def test_delete_user_preserves_path(self):
        from app.router import get_service_url
        result = get_service_url("DELETE", "/api/users/abc123")
        assert result is not None
        target_url, service = result
        assert service == "user-service"
        assert "/api/users/abc123" in target_url

    def test_put_product_preserves_path(self):
        from app.router import get_service_url
        result = get_service_url("PUT", "/api/products/xyz")
        assert result is not None
        target_url, _ = result
        assert "/api/products/xyz" in target_url

    def test_report_sub_path_routes_correctly(self):
        from app.router import get_service_url
        result = get_service_url("GET", "/api/reports/summary")
        assert result is not None
        _, service = result
        assert service == "report-service"
