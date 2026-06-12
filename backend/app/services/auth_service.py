import logging
from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy import select

from app.config import get_settings
from app.database.database import get_session_factory
from app.models.user import User

logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int, role: str, org_id: int | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    if org_id:
        payload["org_id"] = org_id
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def create_refresh_token(user_id: int) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(days=30)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "refresh"}, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def register_user(email: str, password: str, full_name: str = "") -> dict:
    settings = get_settings()
    async with get_session_factory()() as db:
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name or email.split("@")[0],
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        from app.models.organization import Organization
        org = Organization(name=f"{user.full_name}'s Organization", owner_id=user.id)
        db.add(org)
        await db.commit()
        await db.refresh(org)

        user.organization_id = org.id
        await db.commit()

        access = create_access_token(user.id, user.role, org.id)
        refresh = create_refresh_token(user.id)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer",
                "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}}


async def login_user(email: str, password: str) -> dict:
    async with get_session_factory()() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account deactivated")

        user.last_login = datetime.now(timezone.utc)
        await db.commit()

        access = create_access_token(user.id, user.role, user.organization_id)
        refresh = create_refresh_token(user.id)
        return {"access_token": access, "refresh_token": refresh, "token_type": "bearer",
                "user": {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role, "organization_id": user.organization_id}}


async def get_current_user(user_id: int) -> User | None:
    async with get_session_factory()() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
