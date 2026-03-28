"""管理员功能：用户管理 + 批量操作 + 共享管理"""
import json
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.security import hash_password
from app.core.dependencies import require_admin
from app.models.models import (
    User, Channel, NotifierConfig, ChannelSubscription,
    SharedNotifierAccess, NotificationLog, NotificationTemplate, SharedTemplateAccess,
)

router = APIRouter(prefix="/admin")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/users", response_class=HTMLResponse)
async def user_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return tpl.TemplateResponse("admin/users.html", {
        "request": request, "user": user, "users": users,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/users/create")
async def user_create(
    username: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    existing = (await db.execute(select(User).where(User.username == username))).scalar_one_or_none()
    if existing:
        return RedirectResponse("/admin/users?msg=用户名已存在&msg_type=error", status_code=303)
    new_user = User(
        username=username,
        password_hash=hash_password(password),
        is_admin=is_admin,
        must_change_pwd=True,
    )
    db.add(new_user)
    await db.commit()
    return RedirectResponse("/admin/users?msg=用户创建成功&msg_type=success", status_code=303)


@router.post("/users/{uid}/toggle")
async def user_toggle(uid: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    target = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not target:
        return RedirectResponse("/admin/users?msg=用户不存在&msg_type=error", status_code=303)
    if target.id == user.id:
        return RedirectResponse("/admin/users?msg=不能操作自己&msg_type=error", status_code=303)
    target.is_active = not target.is_active
    await db.commit()
    return RedirectResponse(f"/admin/users?msg={'启用' if target.is_active else '禁用'}成功&msg_type=success", status_code=303)


@router.post("/users/{uid}/reset-password")
async def user_reset_password(
    uid: int, new_password: str = Form(...),
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    target = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not target:
        return RedirectResponse("/admin/users?msg=用户不存在&msg_type=error", status_code=303)
    target.password_hash = hash_password(new_password)
    target.must_change_pwd = True
    await db.commit()
    return RedirectResponse("/admin/users?msg=密码已重置&msg_type=success", status_code=303)


@router.post("/users/{uid}/delete")
async def user_delete(uid: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_admin)):
    if uid == user.id:
        return RedirectResponse("/admin/users?msg=不能删除自己&msg_type=error", status_code=303)
    target = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if target:
        await db.delete(target)
        await db.commit()
    return RedirectResponse("/admin/users?msg=用户已删除&msg_type=success", status_code=303)


@router.post("/users/batch")
async def user_batch(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
):
    form = await request.form()
    action = form.get("action", "")
    raw_ids = form.get("user_ids", "")
    ids = [int(x) for x in raw_ids.split(",") if x.strip().isdigit()]
    ids = [x for x in ids if x != user.id]

    if not ids:
        return RedirectResponse("/admin/users?msg=未选择用户&msg_type=warning", status_code=303)

    if action == "enable":
        await db.execute(update(User).where(User.id.in_(ids)).values(is_active=True))
        msg = f"已启用 {len(ids)} 个用户"
    elif action == "disable":
        await db.execute(update(User).where(User.id.in_(ids)).values(is_active=False))
        msg = f"已禁用 {len(ids)} 个用户"
    elif action == "delete":
        await db.execute(delete(User).where(User.id.in_(ids)))
        msg = f"已删除 {len(ids)} 个用户"
    else:
        msg = "未知操作"

    await db.commit()
    return RedirectResponse(f"/admin/users?msg={msg}&msg_type=success", status_code=303)


@router.get("/channels/{channel_id}/share", response_class=HTMLResponse)
async def share_channel_page(
    channel_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)

    all_users = (await db.execute(
        select(User).where(User.id != user.id).order_by(User.username)
    )).scalars().all()

    subs = (await db.execute(
        select(ChannelSubscription).where(ChannelSubscription.channel_id == channel_id)
    )).scalars().all()
    sub_map = {s.user_id: s for s in subs}

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    stats = {}
    for s in subs:
        daily = (await db.execute(
            select(func.count(NotificationLog.id)).where(
                NotificationLog.channel_id == channel_id,
                NotificationLog.user_id == s.user_id,
                NotificationLog.created_at >= day_start,
            )
        )).scalar() or 0
        stats[s.user_id] = daily

    return tpl.TemplateResponse("admin/share_channel.html", {
        "request": request, "user": user, "channel": ch,
        "all_users": all_users, "sub_map": sub_map, "stats": stats,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/channels/{channel_id}/share")
async def share_channel_save(
    channel_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    ch = (await db.execute(
        select(Channel).where(Channel.id == channel_id, Channel.user_id == user.id)
    )).scalar_one_or_none()
    if not ch:
        return RedirectResponse("/channels?msg=频道不存在&msg_type=error", status_code=303)

    form = await request.form()

    ch.per_hour_limit = int(form.get("per_hour_limit", 10))
    ch.per_day_limit = int(form.get("per_day_limit", 50))
    ch.min_interval = int(form.get("min_interval", 30))
    ch.global_hour_limit = int(form.get("global_hour_limit", 100))
    ch.global_day_limit = int(form.get("global_day_limit", 500))

    selected_ids = set()
    for key in form.keys():
        if key.startswith("user_"):
            try:
                selected_ids.add(int(key[5:]))
            except ValueError:
                pass

    existing = (await db.execute(
        select(ChannelSubscription).where(ChannelSubscription.channel_id == channel_id)
    )).scalars().all()
    existing_map = {s.user_id: s for s in existing}

    for uid in selected_ids:
        if uid not in existing_map:
            db.add(ChannelSubscription(channel_id=channel_id, user_id=uid, is_active=False))

    for uid, sub in existing_map.items():
        if uid not in selected_ids:
            await db.delete(sub)

    await db.commit()
    return RedirectResponse(
        f"/admin/channels/{channel_id}/share?msg=共享设置已保存&msg_type=success", status_code=303
    )


@router.get("/notifiers/{nc_id}/share", response_class=HTMLResponse)
async def share_notifier_page(
    nc_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    nc = (await db.execute(
        select(NotifierConfig).where(NotifierConfig.id == nc_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if not nc:
        return RedirectResponse("/notifiers?msg=渠道不存在&msg_type=error", status_code=303)

    all_users = (await db.execute(
        select(User).where(User.id != user.id).order_by(User.username)
    )).scalars().all()

    access_list = (await db.execute(
        select(SharedNotifierAccess).where(SharedNotifierAccess.notifier_config_id == nc_id)
    )).scalars().all()
    access_user_ids = {a.user_id for a in access_list}

    return tpl.TemplateResponse("admin/share_notifier.html", {
        "request": request, "user": user, "notifier": nc,
        "all_users": all_users, "access_user_ids": access_user_ids,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/notifiers/{nc_id}/share")
async def share_notifier_save(
    nc_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    nc = (await db.execute(
        select(NotifierConfig).where(NotifierConfig.id == nc_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if not nc:
        return RedirectResponse("/notifiers?msg=渠道不存在&msg_type=error", status_code=303)

    form = await request.form()
    selected_ids = set()
    for key in form.keys():
        if key.startswith("user_"):
            try:
                selected_ids.add(int(key[5:]))
            except ValueError:
                pass

    existing = (await db.execute(
        select(SharedNotifierAccess).where(SharedNotifierAccess.notifier_config_id == nc_id)
    )).scalars().all()
    existing_map = {a.user_id: a for a in existing}

    for uid in selected_ids:
        if uid not in existing_map:
            db.add(SharedNotifierAccess(notifier_config_id=nc_id, user_id=uid))

    for uid, access in existing_map.items():
        if uid not in selected_ids:
            await db.delete(access)

    await db.commit()
    return RedirectResponse(
        f"/admin/notifiers/{nc_id}/share?msg=共享设置已保存&msg_type=success", status_code=303
    )


@router.get("/templates/{tpl_id}/share", response_class=HTMLResponse)
async def share_template_page(
    tpl_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    item = (await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == tpl_id, NotificationTemplate.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/templates?msg=模板不存在&msg_type=error", status_code=303)

    all_users = (await db.execute(
        select(User).where(User.id != user.id).order_by(User.username)
    )).scalars().all()

    access_list = (await db.execute(
        select(SharedTemplateAccess).where(SharedTemplateAccess.template_id == tpl_id)
    )).scalars().all()
    access_user_ids = {a.user_id for a in access_list}

    return tpl.TemplateResponse("admin/share_template.html", {
        "request": request, "user": user, "template": item,
        "all_users": all_users, "access_user_ids": access_user_ids,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/templates/{tpl_id}/share")
async def share_template_save(
    tpl_id: int, request: Request,
    db: AsyncSession = Depends(get_db), user: User = Depends(require_admin),
):
    item = (await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.id == tpl_id, NotificationTemplate.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/templates?msg=模板不存在&msg_type=error", status_code=303)

    form = await request.form()
    selected_ids = set()
    for key in form.keys():
        if key.startswith("user_"):
            try:
                selected_ids.add(int(key[5:]))
            except ValueError:
                pass

    existing = (await db.execute(
        select(SharedTemplateAccess).where(SharedTemplateAccess.template_id == tpl_id)
    )).scalars().all()
    existing_map = {a.user_id: a for a in existing}

    for uid in selected_ids:
        if uid not in existing_map:
            db.add(SharedTemplateAccess(template_id=tpl_id, user_id=uid))

    for uid, access in existing_map.items():
        if uid not in selected_ids:
            await db.delete(access)

    await db.commit()
    return RedirectResponse(
        f"/admin/templates/{tpl_id}/share?msg=共享设置已保存&msg_type=success", status_code=303
    )
