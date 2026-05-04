"""发送历史 API"""
import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, NotificationLog, Channel
from app.notifiers.registry import get_notifier

router = APIRouter(prefix="/history", tags=["api-history"])


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def log_to_item(item: NotificationLog, include_detail: bool = False) -> dict:
    data = {
        "id": item.id,
        "channel_id": item.channel_id,
        "channel_name": item.channel.name if item.channel else "",
        "webhook_log_id": item.webhook_log_id,
        "notifier_type": item.notifier_type,
        "subject": item.subject,
        "status": item.status,
        "error_message": item.error_message or "",
        "retry_count": item.retry_count,
        "created_at": dt_to_str(item.created_at),
    }

    if include_detail:
        data["body"] = item.body or ""
        data["webhook_log"] = None

        if item.webhook_log:
            data["webhook_log"] = {
                "id": item.webhook_log.id,
                "ip_address": item.webhook_log.ip_address,
                "content_type": item.webhook_log.content_type,
                "filter_passed": bool(item.webhook_log.filter_passed),
                "filter_detail": item.webhook_log.filter_detail or "",
                "created_at": dt_to_str(item.webhook_log.created_at),
            }
    else:
        body = item.body or ""
        data["body_preview"] = body[:180]

    return data


@router.get("")
async def api_history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: str = Query(""),
    channel_id: str = Query(""),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    filters = [NotificationLog.user_id == user.id]

    if status:
        filters.append(NotificationLog.status == status)

    channel_id_int = None
    if channel_id:
        try:
            channel_id_int = int(channel_id)
        except ValueError:
            channel_id_int = None

    if channel_id_int:
        filters.append(NotificationLog.channel_id == channel_id_int)

    if keyword:
        filters.append(
            or_(
                NotificationLog.subject.ilike(f"%{keyword}%"),
                NotificationLog.body.ilike(f"%{keyword}%"),
                NotificationLog.error_message.ilike(f"%{keyword}%"),
            )
        )

    total = (
        await db.execute(
            select(func.count(NotificationLog.id)).where(*filters)
        )
    ).scalar() or 0

    total_pages = max(1, math.ceil(total / page_size))

    rows = (
        await db.execute(
            select(NotificationLog)
            .where(*filters)
            .options(selectinload(NotificationLog.channel))
            .order_by(NotificationLog.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()

    channels = (
        await db.execute(
            select(Channel)
            .where(Channel.user_id == user.id)
            .order_by(Channel.name)
        )
    ).scalars().all()

    return {
        "items": [log_to_item(item) for item in rows],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
        "filters": {
            "status": status,
            "channel_id": channel_id,
            "keyword": keyword,
        },
        "channels": [
            {
                "id": ch.id,
                "name": ch.name,
            }
            for ch in channels
        ],
    }


@router.get("/{item_id}")
async def api_history_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = (
        await db.execute(
            select(NotificationLog)
            .where(
                NotificationLog.id == item_id,
                NotificationLog.user_id == user.id,
            )
            .options(
                selectinload(NotificationLog.channel),
                selectinload(NotificationLog.webhook_log),
            )
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="记录不存在")

    return log_to_item(item, include_detail=True)


@router.post("/{item_id}/resend")
async def api_history_resend(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    nlog = (
        await db.execute(
            select(NotificationLog)
            .where(
                NotificationLog.id == item_id,
                NotificationLog.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not nlog:
        raise HTTPException(status_code=404, detail="记录不存在")

    ch = (
        await db.execute(
            select(Channel)
            .where(Channel.id == nlog.channel_id, Channel.user_id == user.id)
            .options(
                selectinload(Channel.notifier_config),
                selectinload(Channel.template),
            )
        )
    ).scalar_one_or_none()

    if not ch or not ch.notifier_config:
        raise HTTPException(status_code=400, detail="通知渠道配置不存在")

    notifier = get_notifier(ch.notifier_config.notifier_type)
    if not notifier:
        raise HTTPException(status_code=400, detail="通知类型不支持")

    try:
        config = json.loads(ch.notifier_config.config_json or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="通知渠道配置不是有效 JSON")

    body_format = ch.template.body_format if ch.template else "text"

    try:
        success = await notifier.send(
            subject=nlog.subject,
            body=nlog.body,
            body_format=body_format,
            config=config,
        )

        nlog.retry_count += 1

        if success:
            nlog.status = "success"
            nlog.error_message = ""
            await db.commit()
            return {"ok": True, "msg": "重发成功"}

        nlog.status = "failed"
        nlog.error_message = "发送返回失败"
        await db.commit()

        return {"ok": False, "msg": "发送失败"}

    except Exception as e:
        nlog.retry_count += 1
        nlog.status = "failed"
        nlog.error_message = str(e)[:1000]
        await db.commit()

        return {
            "ok": False,
            "msg": f"发送失败: {str(e)}",
        }