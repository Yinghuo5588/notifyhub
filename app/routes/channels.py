"""Webhook 频道管理 —— v2 支持 is_shared"""
import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import (
    User, Channel, NotificationTemplate, NotifierConfig, FilterRule,
    gen_uuid, gen_token,
)

router = APIRouter(prefix="/channels")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def channel_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Channel)
        .where(Channel.user_id == user.id)
        .options(selectinload(Channel.template), selectinload(Channel.notifier_config))
        .order_by(Channel.created_at.desc())
    )
    channels = result.scalars().all()
    return templates.TemplateResponse("channels/list.html", {
        "request": request, "user": user, "channels": channels,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/new", response_class=HTMLResponse)
async def channel_new(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    tpls = (await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.user_id == user.id)
    )).scalars().all()
    ncs = (await db.execute(
        select(NotifierConfig).where(NotifierConfig.user_id == user.id, NotifierConfig.is_active == True)
    )).scalars().all()
    return templates.TemplateResponse("channels/form.html", {
        "request": request, "user": user,
        "channel": None, "templates_list": tpls, "notifiers_list": ncs,
        "filter_rules": [],
    })


@router.post("/new")
async def channel_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    template_id: int = Form(None),
    notifier_config_id: int = Form(None),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = await request.form()
    ch = Channel(
        user_id=user.id,
        name=name,
        description=description,
        template_id=template_id if template_id else None,
        notifier_config_id=notifier_config_id if notifier_config_id else None,
        is_active=is_active,
    )
    # 仅管理员可设置共享
    if user.is_admin:
        ch.is_shared = "is_shared" in form
    db.add(ch)
    await db.commit()
    return RedirectResponse(f"/channels/{ch.id}/edit?msg=频道创建成功&msg_type=success", status_code=303)


@router.get("/{channel_id}/edit", response_class=HTMLResponse)
async def channel_edit(
    channel_id: int, request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ch = (await db.execute(
        select(Channel)
        .where(Channel.id == channel_id, Channel.user_id == user.id)
        .options(selectinload(Channel.filter_rules))
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)

    tpls = (await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.user_id == user.id)
    )).scalars().all()
    ncs = (await db.execute(
        select(NotifierConfig).where(NotifierConfig.user_id == user.id)
    )).scalars().all()
    return templates.TemplateResponse("channels/form.html", {
        "request": request, "user": user,
        "channel": ch, "templates_list": tpls, "notifiers_list": ncs,
        "filter_rules": ch.filter_rules,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/{channel_id}/edit")
async def channel_update(
    channel_id: int, request: Request,
    name: str = Form(...),
    description: str = Form(""),
    template_id: int = Form(None),
    notifier_config_id: int = Form(None),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)

    form = await request.form()
    ch.name = name
    ch.description = description
    ch.template_id = template_id if template_id else None
    ch.notifier_config_id = notifier_config_id if notifier_config_id else None
    ch.is_active = is_active
    if user.is_admin:
        ch.is_shared = "is_shared" in form
    await db.commit()
    return RedirectResponse(f"/channels/{ch.id}/edit?msg=保存成功&msg_type=success", status_code=303)


@router.post("/{channel_id}/regenerate-token")
async def regenerate_token(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)
    ch.token = gen_token()
    await db.commit()
    return RedirectResponse(f"/channels/{ch.id}/edit?msg=Token已重新生成&msg_type=success", status_code=303)


@router.post("/{channel_id}/delete")
async def channel_delete(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if ch:
        await db.delete(ch)
        await db.commit()
    return RedirectResponse("/channels?msg=频道已删除&msg_type=success", status_code=303)