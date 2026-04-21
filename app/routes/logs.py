"""Webhook 原始请求日志"""
import json
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, WebhookLog, Channel

router = APIRouter(prefix="/logs")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))
PAGE_SIZE = 5


@router.get("/", response_class=HTMLResponse)
async def log_list(
    request: Request,
    page: int = Query(1, ge=1),
    channel_id: str = Query("", alias="channel_id"),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    try:
        channel_id_int = int(channel_id) if channel_id else None
    except ValueError:
        channel_id_int = None

    base_filter = WebhookLog.user_id == user.id
    if channel_id_int:
        base_filter = base_filter & (WebhookLog.channel_id == channel_id_int)
    if keyword:
        base_filter = base_filter & (
            WebhookLog.request_path.ilike(f"%{keyword}%") |
            WebhookLog.http_method.ilike(f"%{keyword}%")
        )

    count_query = select(func.count(WebhookLog.id)).where(base_filter)
    total = (await db.execute(count_query)).scalar() or 0
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    items = (await db.execute(
        select(WebhookLog)
        .where(base_filter)
        .order_by(WebhookLog.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )).scalars().all()

    channels = (await db.execute(
        select(Channel).where(Channel.user_id == user.id).order_by(Channel.name)
    )).scalars().all()

    return tpl.TemplateResponse("logs/list.html", {
        "request": request, "user": user, "items": items,
        "page": page, "total_pages": total_pages, "total": total,
        "channel_id": channel_id, "keyword": keyword, "channels": channels,
    })


@router.get("/{item_id}", response_class=HTMLResponse)
async def log_detail(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(WebhookLog)
        .where(WebhookLog.id == item_id, WebhookLog.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/logs?msg=日志不存在&msg_type=error", status_code=303)

    parsed = {}
    try:
        parsed = json.loads(item.parsed_data) if item.parsed_data else {}
    except Exception:
        pass
    formatted_data = json.dumps(parsed, ensure_ascii=False, indent=2) if parsed else item.parsed_data

    headers = {}
    try:
        headers = json.loads(item.request_headers) if item.request_headers else {}
    except Exception:
        pass
    formatted_headers = json.dumps(headers, ensure_ascii=False, indent=2) if headers else item.request_headers

    return tpl.TemplateResponse("logs/detail.html", {
        "request": request, "user": user, "item": item,
        "formatted_data": formatted_data,
        "formatted_headers": formatted_headers,
    })
