"""设置 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import JWT_EXPIRE_HOURS
from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.core.security import verify_password, hash_password, create_access_token
from app.models.models import User

router = APIRouter(prefix="/settings", tags=["api-settings"])


class ProfileUpdateReq(BaseModel):
    username: str
    email: str | None = ""


class PasswordUpdateReq(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


def user_to_resp(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "is_admin": bool(user.is_admin),
        "is_active": bool(user.is_active),
        "must_change_pwd": bool(user.must_change_pwd),
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/profile")
async def api_get_profile(
    user: User = Depends(get_current_api_user),
):
    return user_to_resp(user)


@router.put("/profile")
async def api_update_profile(
    payload: ProfileUpdateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    username = payload.username.strip()
    email = (payload.email or "").strip()

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    existing = (
        await db.execute(
            select(User).where(
                User.username == username,
                User.id != user.id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    user.username = username
    user.email = email

    await db.commit()
    await db.refresh(user)

    return user_to_resp(user)


@router.put("/password")
async def api_update_password(
    payload: PasswordUpdateReq,
    response: Response,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")

    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码至少 6 位")

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="两次密码不一致")

    user.password_hash = hash_password(payload.new_password)
    user.must_change_pwd = False

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id, user.is_admin)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=JWT_EXPIRE_HOURS * 3600,
    )

    return user_to_resp(user)