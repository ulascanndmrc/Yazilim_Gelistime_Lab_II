from fastapi import APIRouter, HTTPException, Header
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext

from app.models import UserCreate, UserLogin, TokenResponse, UserResponse
from app.database import get_db
from app.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _verify_internal_key(x_internal_api_key: Optional[str]) -> None:
    """Reject requests that don't come from the Dispatcher."""
    if x_internal_api_key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Forbidden: direct access not allowed")


def _create_token(user_id: str, username: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=settings.jwt_expire_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


@router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(
    body: UserCreate,
    x_internal_api_key: Optional[str] = Header(None),
):
    _verify_internal_key(x_internal_api_key)
    db = get_db()

    if await db.users.find_one({"username": body.username}):
        raise HTTPException(status_code=409, detail="Username already exists")
    if await db.users.find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="Email already exists")

    hashed = pwd_context.hash(body.password)
    now = datetime.utcnow()
    doc = {
        "username": body.username,
        "email": body.email,
        "password_hash": hashed,
        "role": body.role,
        "created_at": now,
    }
    result = await db.users.insert_one(doc)
    return UserResponse(
        id=str(result.inserted_id),
        username=body.username,
        email=body.email,
        role=body.role,
        created_at=now,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    body: UserLogin,
    x_internal_api_key: Optional[str] = Header(None),
):
    _verify_internal_key(x_internal_api_key)
    db = get_db()

    user = await db.users.find_one({"username": body.username})
    if not user or not pwd_context.verify(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _create_token(str(user["_id"]), user["username"], user["role"])
    return TokenResponse(
        access_token=token,
        user_id=str(user["_id"]),
        username=user["username"],
        role=user["role"],
    )


@router.get("/auth/validate")
async def validate(x_internal_api_key: Optional[str] = Header(None)):
    _verify_internal_key(x_internal_api_key)
    return {"status": "ok"}


@router.get("/health")
async def health():
    return {"status": "healthy", "service": "login-service"}
