"""FastAPI 依赖注入函数"""
from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.models import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """从cookie中解析JWT，获取当前登录用户"""
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )

    user_id = int(payload.get("sub", 0))
    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_302_FOUND,
            headers={"Location": "/login"},
        )
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """要求管理员权限"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


async def get_current_api_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    API 专用登录依赖。

    与 get_current_user 的区别:
    - 旧页面未登录时 302 跳转 /login
    - API 未登录时返回 401 JSON
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    user_id = int(payload.get("sub", 0))
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )

    return user


async def require_api_admin(
    current_user: User = Depends(get_current_api_user),
) -> User:
    """API 专用管理员权限依赖。"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user