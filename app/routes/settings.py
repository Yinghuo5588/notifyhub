"""用户设置"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.security import verify_password, hash_password, create_access_token
from app.core.dependencies import get_current_user
from app.models.models import User

router = APIRouter(prefix="/settings")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    user: User = Depends(get_current_user),
):
    return tpl.TemplateResponse("settings.html", {
        "request": request, "user": user,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/password")
async def change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(old_password, user.password_hash):
        return RedirectResponse("/settings?msg=原密码错误&msg_type=error", status_code=303)

    if len(new_password) < 6:
        return RedirectResponse("/settings?msg=新密码至少6位&msg_type=error", status_code=303)

    if new_password != confirm_password:
        return RedirectResponse("/settings?msg=两次密码不一致&msg_type=error", status_code=303)

    user.password_hash = hash_password(new_password)
    user.must_change_pwd = False
    await db.commit()

    # 重新生成token
    token = create_access_token(user.id, user.is_admin)
    response = RedirectResponse("/settings?msg=密码修改成功&msg_type=success", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="lax", max_age=3600 * 72)
    return response


@router.post("/profile")
async def update_profile(
    request: Request,
    username: str = Form(""),
    email: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if username.strip():
        user.username = username.strip()
    user.email = email
    await db.commit()
    return RedirectResponse("/settings?msg=资料已更新&msg_type=success", status_code=303)