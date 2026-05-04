"""Webhook 请求日志 API"""
import json
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, WebhookLog, Channel

router = APIRouter(prefix="/logs", tags=["api-logs"])


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def parse_json_text(value: str, fallback):
    try:
        return json.loads(value) if value else fallback
    except Exception:
        return fallback


def log_to_item(item: WebhookLog, include_detail: bool = False) -> dict:
    parsed_data = parse_json_text(item.parsed_data or "{}", {})
    request_headers = parse_json_text(item.request_headers or "{}", {})

    data = {
        "id": item.id,
        "channel_id": item.channel_id,
        "channel_name": item.channel.name if item.channel else "",
        "content_type": item.content_type or "",
        "ip_address": item.ip_address or "",
        "filter_passed": bool(item.filter_passed),
        "filter_detail": item.filter_detail or "",
        "created_at": dt_to_str(item.created_at),
    }

    if include_detail:
        data.update(
            {
                "request_headers": request_headers,
                "request_body": item.request_body or "",
                "parsed_data": parsed_data,
            }
        )
    else:
        preview = ""
        if isinstance(parsed_data, dict):
            preview = json.dumps(parsed_data, ensure_ascii=False)[:180]
        else:
            preview = str(parsed_data)[:180]

        data["data_preview"] = preview

    return data


@router.get("")
async def api_log_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    channel_id: str = Query(""),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    filters = [WebhookLog.user_id == user.id]

    channel_id_int = None
    if channel_id:
        try:
            channel_id_int = int(channel_id)
        except ValueError:
            channel_id_int = None

    if channel_id_int:
        filters.append(WebhookLog.channel_id == channel_id_int)

    if keyword:
        # 当前模型字段：request_headers、request_body、parsed_data、ip_address、content_type、filter_detail
        filters.append(
            or_(
                WebhookLog.request_body.ilike(f"%{keyword}%"),
                WebhookLog.parsed_data.ilike(f"%{keyword}%"),
                WebhookLog.request_headers.ilike(f"%{keyword}%"),
                WebhookLog.ip_address.ilike(f"%{keyword}%"),
                WebhookLog.content_type.ilike(f"%{keyword}%"),
                WebhookLog.filter_detail.ilike(f"%{keyword}%"),
            )
        )

    total = (
        await db.execute(
            select(func.count(WebhookLog.id)).where(*filters)
        )
    ).scalar() or 0

    total_pages = max(1, math.ceil(total / page_size))

    rows = (
        await db.execute(
            select(WebhookLog)
            .where(*filters)
            .options(selectinload(WebhookLog.channel))
            .order_by(WebhookLog.created_at.desc())
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
async def api_log_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = (
        await db.execute(
            select(WebhookLog)
            .where(
                WebhookLog.id == item_id,
                WebhookLog.user_id == user.id,
            )
            .options(selectinload(WebhookLog.channel))
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="日志不存在")

    return log_to_item(item, include_detail=True)