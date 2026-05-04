"""管理员 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_api_admin
from app.core.security import hash_password
from app.models.models import (
    User,
    Channel,
    ChannelSubscription,
    NotifierConfig,
    SharedNotifierAccess,
    NotificationTemplate,
    SharedTemplateAccess,
    NotificationLog,
)

router = APIRouter(prefix="/admin", tags=["api-admin"])


class UserCreateReq(BaseModel):
    username: str
    password: str
    email: str = ""
    is_admin: bool = False


class UserBatchReq(BaseModel):
    action: str
    user_ids: list[int]


class ResetPasswordReq(BaseModel):
    new_password: str


class ShareUsersReq(BaseModel):
    user_ids: list[int]


class ShareChannelReq(BaseModel):
    user_ids: list[int]
    per_hour_limit: int = 10
    per_day_limit: int = 50
    min_interval: int = 30
    global_hour_limit: int = 100
    global_day_limit: int = 500


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def user_to_item(user: User) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email or "",
        "is_admin": bool(user.is_admin),
        "is_active": bool(user.is_active),
        "must_change_pwd": bool(user.must_change_pwd),
        "created_at": dt_to_str(user.created_at),
    }


async def get_user_or_404(uid: int, db: AsyncSession) -> User:
    target = (
        await db.execute(select(User).where(User.id == uid))
    ).scalar_one_or_none()

    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")

    return target


@router.get("/users")
async def api_admin_user_list(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    rows = (
        await db.execute(
            select(User).order_by(User.created_at.desc())
        )
    ).scalars().all()

    return [user_to_item(item) for item in rows]


@router.post("/users")
async def api_admin_user_create(
    payload: UserCreateReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    username = payload.username.strip()
    password = payload.password

    if not username:
        raise HTTPException(status_code=400, detail="用户名不能为空")

    if len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    existing = (
        await db.execute(select(User).where(User.username == username))
    ).scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    item = User(
        username=username,
        email=payload.email.strip(),
        password_hash=hash_password(password),
        is_admin=payload.is_admin,
        must_change_pwd=True,
    )

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return user_to_item(item)


@router.post("/users/{uid}/toggle")
async def api_admin_user_toggle(
    uid: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    if uid == admin.id:
        raise HTTPException(status_code=400, detail="不能操作当前登录用户")

    target = await get_user_or_404(uid, db)
    target.is_active = not target.is_active

    await db.commit()
    await db.refresh(target)

    return user_to_item(target)


@router.post("/users/{uid}/reset-password")
async def api_admin_user_reset_password(
    uid: int,
    payload: ResetPasswordReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    target = await get_user_or_404(uid, db)
    target.password_hash = hash_password(payload.new_password)
    target.must_change_pwd = True

    await db.commit()
    await db.refresh(target)

    return user_to_item(target)


@router.delete("/users/{uid}")
async def api_admin_user_delete(
    uid: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    if uid == admin.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录用户")

    target = await get_user_or_404(uid, db)

    await db.delete(target)
    await db.commit()

    return {"ok": True}


@router.post("/users/batch")
async def api_admin_user_batch(
    payload: UserBatchReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    ids = [uid for uid in payload.user_ids if uid != admin.id]

    if not ids:
        raise HTTPException(status_code=400, detail="未选择可操作用户")

    if payload.action == "enable":
        await db.execute(update(User).where(User.id.in_(ids)).values(is_active=True))
    elif payload.action == "disable":
        await db.execute(update(User).where(User.id.in_(ids)).values(is_active=False))
    elif payload.action == "delete":
        await db.execute(delete(User).where(User.id.in_(ids)))
    else:
        raise HTTPException(status_code=400, detail="未知批量操作")

    await db.commit()

    return {"ok": True, "count": len(ids)}


@router.get("/channels/{channel_id}/share")
async def api_admin_share_channel_get(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    ch = (
        await db.execute(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not ch:
        raise HTTPException(status_code=404, detail="频道不存在")

    users = (
        await db.execute(
            select(User)
            .where(User.id != admin.id)
            .order_by(User.username)
        )
    ).scalars().all()

    subs = (
        await db.execute(
            select(ChannelSubscription)
            .where(ChannelSubscription.channel_id == channel_id)
            .options(selectinload(ChannelSubscription.user))
        )
    ).scalars().all()

    sub_map = {sub.user_id: sub for sub in subs}

    stats = {}
    for sub in subs:
        daily = (
            await db.execute(
                select(func.count(NotificationLog.id)).where(
                    NotificationLog.channel_id == channel_id,
                    NotificationLog.user_id == sub.user_id,
                )
            )
        ).scalar() or 0
        stats[sub.user_id] = daily

    return {
        "channel": {
            "id": ch.id,
            "name": ch.name,
            "description": ch.description or "",
            "is_shared": bool(ch.is_shared),
            "per_hour_limit": ch.per_hour_limit,
            "per_day_limit": ch.per_day_limit,
            "min_interval": ch.min_interval,
            "global_hour_limit": ch.global_hour_limit,
            "global_day_limit": ch.global_day_limit,
        },
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email or "",
                "is_active": bool(u.is_active),
                "selected": u.id in sub_map,
                "subscription_active": bool(sub_map[u.id].is_active) if u.id in sub_map else False,
                "sends_today": stats.get(u.id, 0),
            }
            for u in users
        ],
    }


@router.put("/channels/{channel_id}/share")
async def api_admin_share_channel_save(
    channel_id: int,
    payload: ShareChannelReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    ch = (
        await db.execute(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not ch:
        raise HTTPException(status_code=404, detail="频道不存在")

    ch.is_shared = True
    ch.per_hour_limit = max(1, payload.per_hour_limit)
    ch.per_day_limit = max(1, payload.per_day_limit)
    ch.min_interval = max(0, payload.min_interval)
    ch.global_hour_limit = max(1, payload.global_hour_limit)
    ch.global_day_limit = max(1, payload.global_day_limit)

    selected = set(payload.user_ids)

    existing = (
        await db.execute(
            select(ChannelSubscription).where(
                ChannelSubscription.channel_id == channel_id
            )
        )
    ).scalars().all()

    existing_map = {item.user_id: item for item in existing}

    for uid in selected:
        if uid == admin.id:
            continue
        if uid not in existing_map:
            db.add(
                ChannelSubscription(
                    channel_id=channel_id,
                    user_id=uid,
                    is_active=False,
                )
            )

    for uid, sub in existing_map.items():
        if uid not in selected:
            await db.delete(sub)

    await db.commit()

    return {"ok": True}


@router.get("/notifiers/{nc_id}/share")
async def api_admin_share_notifier_get(
    nc_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    nc = (
        await db.execute(
            select(NotifierConfig).where(
                NotifierConfig.id == nc_id,
                NotifierConfig.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not nc:
        raise HTTPException(status_code=404, detail="通知渠道不存在")

    users = (
        await db.execute(
            select(User)
            .where(User.id != admin.id)
            .order_by(User.username)
        )
    ).scalars().all()

    access = (
        await db.execute(
            select(SharedNotifierAccess).where(
                SharedNotifierAccess.notifier_config_id == nc_id
            )
        )
    ).scalars().all()

    access_ids = {item.user_id for item in access}

    return {
        "notifier": {
            "id": nc.id,
            "name": nc.name,
            "notifier_type": nc.notifier_type,
            "is_shared": bool(nc.is_shared),
        },
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email or "",
                "is_active": bool(u.is_active),
                "selected": u.id in access_ids,
            }
            for u in users
        ],
    }


@router.put("/notifiers/{nc_id}/share")
async def api_admin_share_notifier_save(
    nc_id: int,
    payload: ShareUsersReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    nc = (
        await db.execute(
            select(NotifierConfig).where(
                NotifierConfig.id == nc_id,
                NotifierConfig.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not nc:
        raise HTTPException(status_code=404, detail="通知渠道不存在")

    nc.is_shared = True
    selected = set(uid for uid in payload.user_ids if uid != admin.id)

    existing = (
        await db.execute(
            select(SharedNotifierAccess).where(
                SharedNotifierAccess.notifier_config_id == nc_id
            )
        )
    ).scalars().all()

    existing_map = {item.user_id: item for item in existing}

    for uid in selected:
        if uid not in existing_map:
            db.add(SharedNotifierAccess(notifier_config_id=nc_id, user_id=uid))

    for uid, item in existing_map.items():
        if uid not in selected:
            await db.delete(item)

    await db.commit()

    return {"ok": True}


@router.get("/templates/{tpl_id}/share")
async def api_admin_share_template_get(
    tpl_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    tpl = (
        await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == tpl_id,
                NotificationTemplate.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    users = (
        await db.execute(
            select(User)
            .where(User.id != admin.id)
            .order_by(User.username)
        )
    ).scalars().all()

    access = (
        await db.execute(
            select(SharedTemplateAccess).where(
                SharedTemplateAccess.template_id == tpl_id
            )
        )
    ).scalars().all()

    access_ids = {item.user_id for item in access}

    return {
        "template": {
            "id": tpl.id,
            "name": tpl.name,
            "description": tpl.description or "",
            "is_shared": bool(tpl.is_shared),
        },
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email or "",
                "is_active": bool(u.is_active),
                "selected": u.id in access_ids,
            }
            for u in users
        ],
    }


@router.put("/templates/{tpl_id}/share")
async def api_admin_share_template_save(
    tpl_id: int,
    payload: ShareUsersReq,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_api_admin),
):
    tpl = (
        await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == tpl_id,
                NotificationTemplate.user_id == admin.id,
            )
        )
    ).scalar_one_or_none()

    if not tpl:
        raise HTTPException(status_code=404, detail="模板不存在")

    tpl.is_shared = True
    selected = set(uid for uid in payload.user_ids if uid != admin.id)

    existing = (
        await db.execute(
            select(SharedTemplateAccess).where(
                SharedTemplateAccess.template_id == tpl_id
            )
        )
    ).scalars().all()

    existing_map = {item.user_id: item for item in existing}

    for uid in selected:
        if uid not in existing_map:
            db.add(SharedTemplateAccess(template_id=tpl_id, user_id=uid))

    for uid, item in existing_map.items():
        if uid not in selected:
            await db.delete(item)

    await db.commit()

    return {"ok": True}