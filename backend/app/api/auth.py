from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel

from app.services.auth_service import register_user, login_user, decode_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


def get_user_id_from_token(authorization: str = Header("")) -> int:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    payload = decode_token(token)
    return int(payload["sub"])


@router.post("/register")
async def register(payload: RegisterRequest):
    return await register_user(payload.email, payload.password, payload.full_name)


@router.post("/login")
async def login(payload: LoginRequest):
    return await login_user(payload.email, payload.password)


@router.post("/refresh")
async def refresh(payload: RefreshRequest):
    payload_data = decode_token(payload.refresh_token)
    if payload_data.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Invalid refresh token")
    user = await get_current_user(int(payload_data["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    from app.services.auth_service import create_access_token, create_refresh_token
    access = create_access_token(user.id, user.role, user.organization_id)
    ref = create_refresh_token(user.id)
    return {"access_token": access, "refresh_token": ref, "token_type": "bearer"}


@router.get("/me")
async def me(user_id: int = Depends(get_user_id_from_token)):
    user = await get_current_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "organization_id": user.organization_id,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": str(user.created_at) if user.created_at else None,
    }
