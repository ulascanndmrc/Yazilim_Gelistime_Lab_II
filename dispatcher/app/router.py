"""
GREEN PHASE: Service router implementation satisfying TDD routing tests.
Maps URL prefixes to microservice targets.
"""
from typing import Optional, Tuple
from app.config import settings


class ServiceRoute:
    """Routing rule mapping a URL prefix to a microservice."""

    def __init__(self, prefix: str, service_url: str, service_name: str):
        self.prefix = prefix
        self.service_url = service_url
        self.service_name = service_name

    def matches(self, path: str) -> bool:
        return path.startswith(self.prefix)

    def build_target_url(self, path: str) -> str:
        return f"{self.service_url}{path}"


class ServiceRouter:
    """Routes requests to microservices based on URL prefix matching."""

    def __init__(self):
        self._routes: list = []

    def add_route(self, prefix: str, service_url: str, service_name: str) -> None:
        self._routes.append(ServiceRoute(prefix, service_url, service_name))

    def resolve(self, path: str) -> Optional[Tuple[str, str]]:
        """Return (target_url, service_name) or None if no route matches."""
        for route in self._routes:
            if route.matches(path):
                return route.build_target_url(path), route.service_name
        return None


# Module-level singleton router
_router = ServiceRouter()
_router.add_route("/auth/",          settings.login_service_url,   "login-service")
_router.add_route("/api/messages",   settings.message_service_url, "message-service")
_router.add_route("/api/users",      settings.user_service_url,    "user-service")
_router.add_route("/api/products",   settings.product_service_url, "product-service")
_router.add_route("/api/reports",    settings.report_service_url,  "report-service")


def get_service_url(method: str, path: str) -> Optional[Tuple[str, str]]:
    """Resolve a path to (target_url, service_name). Returns None if not found."""
    return _router.resolve(path)
