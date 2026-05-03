"""认证 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import JWT_EXPIRE_HOURS
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.dependencies import get_current_api_user
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["api-auth"])


class LoginReq(BaseModel):
    username: str
    password: str


class UserResp(BaseModel):
    id: int
    username: str
    email: str = ""
    is_admin: bool
    is_active: bool = True
    must_change_pwd: bool = False


def user_to_resp(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "is_admin": bool(user.is_admin),
        "is_active": bool(user.is_active),
        "must_change_pwd": bool(user.must_change_pwd),
    }


@router.post("/login", response_model=UserResp)
async def api_login(
    payload: LoginReq,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.username == payload.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")

    token = create_access_token(user.id, user.is_admin)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
    )

    return user_to_resp(user)


@router.post("/logout")
async def api_logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserResp)
async def api_me(user: User = Depends(get_current_api_user)):
    return user_to_resp(user)