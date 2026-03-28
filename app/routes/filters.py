"""过滤规则管理（在频道编辑页面内使用，HTMX局部刷新）"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, Channel, FilterRule

router = APIRouter(prefix="/filters")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.post("/add")
async def filter_add(
    channel_id: int = Form(...),
    name: str = Form(""),
    field_path: str = Form(""),
    match_type: str = Form("keyword"),
    pattern: str = Form(...),
    mode: str = Form("blacklist"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # 验证频道归属
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)

    rule = FilterRule(
        channel_id=channel_id,
        user_id=user.id,
        name=name,
        field_path=field_path,
        match_type=match_type,
        pattern=pattern,
        mode=mode,
    )
    db.add(rule)
    await db.commit()
    return RedirectResponse(f"/channels/{channel_id}/edit?msg=规则已添加&msg_type=success", status_code=303)


@router.post("/{rule_id}/delete")
async def filter_delete(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rule = (await db.execute(
        select(FilterRule).where(FilterRule.id == rule_id, FilterRule.user_id == user.id)
    )).scalar_one_or_none()
    channel_id = rule.channel_id if rule else None
    if rule:
        await db.delete(rule)
        await db.commit()
    if channel_id:
        return RedirectResponse(f"/channels/{channel_id}/edit?msg=规则已删除&msg_type=success", status_code=303)
    return RedirectResponse("/channels", status_code=303)


@router.post("/{rule_id}/toggle")
async def filter_toggle(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rule = (await db.execute(
        select(FilterRule).where(FilterRule.id == rule_id, FilterRule.user_id == user.id)
    )).scalar_one_or_none()
    if rule:
        rule.is_active = not rule.is_active
        await db.commit()
        return RedirectResponse(
            f"/channels/{rule.channel_id}/edit?msg=规则已{'启用' if rule.is_active else '禁用'}&msg_type=success",
            status_code=303,
        )
    return RedirectResponse("/channels", status_code=303)