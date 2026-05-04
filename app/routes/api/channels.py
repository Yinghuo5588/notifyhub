"""频道 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, Channel

router = APIRouter(prefix="/channels", tags=["api-channels"])


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def channel_to_item(ch: Channel) -> dict:
    return {
        "id": ch.id,
        "name": ch.name,
        "description": ch.description or "",
        "channel_uuid": ch.channel_uuid,
        "token": ch.token,
        "template_id": ch.template_id,
        "template_name": ch.template.name if ch.template else "",
        "notifier_config_id": ch.notifier_config_id,
        "notifier_name": ch.notifier_config.name if ch.notifier_config else "",
        "notifier_type": ch.notifier_config.notifier_type if ch.notifier_config else "",
        "is_active": bool(ch.is_active),
        "is_shared": bool(ch.is_shared),
        "per_hour_limit": ch.per_hour_limit,
        "per_day_limit": ch.per_day_limit,
        "min_interval": ch.min_interval,
        "global_hour_limit": ch.global_hour_limit,
        "global_day_limit": ch.global_day_limit,
        "created_at": dt_to_str(ch.created_at),
        "updated_at": dt_to_str(ch.updated_at),
    }


@router.get("")
async def api_channel_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    result = await db.execute(
        select(Channel)
        .where(Channel.user_id == user.id)
        .options(
            selectinload(Channel.template),
            selectinload(Channel.notifier_config),
        )
        .order_by(Channel.created_at.desc())
    )
    rows = result.scalars().all()

    return [channel_to_item(ch) for ch in rows]


@router.delete("/{channel_id}")
async def api_channel_delete(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    ch = (
        await db.execute(
            select(Channel).where(
                Channel.id == channel_id,
                Channel.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not ch:
        raise HTTPException(status_code=404, detail="频道不存在")

    await db.delete(ch)
    await db.commit()

    return {"ok": True}