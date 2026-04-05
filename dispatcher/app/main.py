"""
Dispatcher (API Gateway) — Main Application
Central entry point routing all external traffic to microservices.
"""
import time
from contextlib import asynccontextmanager
from typing import Optional

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.database import connect_to_mongo, close_mongo_connection, get_db
from app.auth_middleware import (
    validate_token, extract_token_from_header, is_public_route,
    MissingTokenError, TokenExpiredError, InvalidTokenError,
)
from app.logger import RequestLogger
from app.router import get_service_url

# ─── Prometheus Metrics ───────────────────────────────────────────────────────
REQUEST_COUNT = Counter(
    "dispatcher_requests_total", "Total requests",
    ["method", "service", "status_code"])
REQUEST_LATENCY = Histogram(
    "dispatcher_request_duration_seconds", "Request latency",
    ["method", "service"])


# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


# ─── App ──────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Dispatcher – API Gateway",
    description="Central gateway for all microservices traffic",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Internal Routes ──────────────────────────────────────────────────────────
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "dispatcher"}


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/gateway/stats")
async def gateway_stats():
    logger = RequestLogger(get_db())
    return await logger.get_statistics()


@app.get("/api/gateway/logs")
async def gateway_logs(limit: int = 100):
    logger = RequestLogger(get_db())
    logs = await logger.get_recent_logs(limit)
    return {"logs": logs, "count": len(logs)}


@app.get("/api/gateway/health")
async def services_health():
    services = {
        "login-service":   settings.login_service_url,
        "message-service": settings.message_service_url,
        "user-service":    settings.user_service_url,
        "product-service": settings.product_service_url,
        "report-service":  settings.report_service_url,
    }
    result = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in services.items():
            try:
                resp = await client.get(f"{url}/health")
                status = "up" if resp.status_code == 200 else "degraded"
                result[name] = {"status": status, "code": resp.status_code}
            except Exception as e:
                result[name] = {"status": "down", "error": str(e)}
    return result


# ─── Proxy Handler ────────────────────────────────────────────────────────────
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    full_path = f"/{path}"
    method = request.method
    start = time.time()
    user_id: Optional[str] = None
    service_name = "unknown"

    # 1. JWT authentication (skip public routes)
    if not is_public_route(method, full_path):
        token = extract_token_from_header(request.headers.get("Authorization"))
        try:
            payload = validate_token(token, settings.jwt_secret)
            user_id = payload.get("sub")
        except MissingTokenError as e:
            elapsed = (time.time() - start) * 1000
            await _log(method, full_path, None, service_name, 401, elapsed, str(e.detail), request)
            return JSONResponse(status_code=401, content={"detail": e.detail})
        except TokenExpiredError as e:
            elapsed = (time.time() - start) * 1000
            await _log(method, full_path, None, service_name, 401, elapsed, str(e.detail), request)
            return JSONResponse(status_code=401, content={"detail": e.detail})
        except InvalidTokenError as e:
            elapsed = (time.time() - start) * 1000
            await _log(method, full_path, None, service_name, 401, elapsed, str(e.detail), request)
            return JSONResponse(status_code=401, content={"detail": e.detail})

    # 2. Route resolution
    route_result = get_service_url(method, full_path)
    if route_result is None:
        elapsed = (time.time() - start) * 1000
        await _log(method, full_path, user_id, "none", 404, elapsed, "No route", request)
        return JSONResponse(status_code=404, content={"detail": f"No service for path: {full_path}"})

    target_url, service_name = route_result

    # 3. Forward request
    try:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in ("host", "content-length")}
        headers["X-Internal-Api-Key"] = settings.internal_api_key
        if user_id:
            headers["X-User-Id"] = user_id

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.request(
                method=method, url=target_url, headers=headers,
                content=body, params=dict(request.query_params))

        elapsed = (time.time() - start) * 1000
        REQUEST_COUNT.labels(method=method, service=service_name,
                             status_code=str(resp.status_code)).inc()
        REQUEST_LATENCY.labels(method=method, service=service_name).observe(elapsed / 1000)
        await _log(method, full_path, user_id, service_name, resp.status_code, elapsed, None, request)

        resp_headers = {k: v for k, v in resp.headers.items()
                        if k.lower() not in ("content-encoding", "transfer-encoding", "connection")}
        return Response(content=resp.content, status_code=resp.status_code,
                        headers=resp_headers,
                        media_type=resp.headers.get("content-type", "application/json"))

    except httpx.ConnectError:
        elapsed = (time.time() - start) * 1000
        REQUEST_COUNT.labels(method=method, service=service_name, status_code="503").inc()
        await _log(method, full_path, user_id, service_name, 503, elapsed, "Service unavailable", request)
        return JSONResponse(status_code=503, content={"detail": f"'{service_name}' is unavailable"})

    except httpx.TimeoutException:
        elapsed = (time.time() - start) * 1000
        REQUEST_COUNT.labels(method=method, service=service_name, status_code="504").inc()
        await _log(method, full_path, user_id, service_name, 504, elapsed, "Gateway timeout", request)
        return JSONResponse(status_code=504, content={"detail": f"'{service_name}' timed out"})

    except Exception as e:
        elapsed = (time.time() - start) * 1000
        await _log(method, full_path, user_id, service_name, 502, elapsed, str(e), request)
        return JSONResponse(status_code=502, content={"detail": "Bad gateway"})


async def _log(method, path, user_id, service, status, elapsed, error, request):
    try:
        logger = RequestLogger(get_db())
        await logger.log_request(
            method=method, path=path, user_id=user_id,
            target_service=service, status_code=status,
            response_time_ms=elapsed, error=error,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        pass
