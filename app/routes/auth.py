"""认证路由：登录、登出、修改密码"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.models import User

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": request.query_params.get("error", ""),
    })


@router.post("/login")
async def login_action(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=用户名或密码错误", status_code=303)

    if not user.is_active:
        return RedirectResponse("/login?error=账号已被禁用", status_code=303)

    token = create_access_token(user.id, user.is_admin)

    # 首次登录需要改密码
    if user.must_change_pwd:
        response = RedirectResponse("/settings?msg=首次登录请修改默认密码&msg_type=warning", status_code=303)
    else:
        response = RedirectResponse("/", status_code=303)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600 * 72,
    )
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response