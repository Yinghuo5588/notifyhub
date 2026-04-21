"""通知发送历史"""
import json
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, NotificationLog, Channel, NotifierConfig
from app.notifiers.registry import get_notifier

router = APIRouter(prefix="/history")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))
PAGE_SIZE = 5


@router.get("/", response_class=HTMLResponse)
async def history_list(
    request: Request,
    page: int = Query(1, ge=1),
    status: str = Query(""),
    channel_id: int = Query(None),
    keyword: str = Query(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    base_filter = NotificationLog.user_id == user.id
    if status:
        base_filter = base_filter & (NotificationLog.status == status)
    if channel_id:
        base_filter = base_filter & (NotificationLog.channel_id == channel_id)
    if keyword:
        base_filter = base_filter & (
            NotificationLog.subject.ilike(f"%{keyword}%") |
            NotificationLog.body.ilike(f"%{keyword}%")
        )

    count_query = select(func.count(NotificationLog.id)).where(base_filter)
    total = (await db.execute(count_query)).scalar() or 0
    total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)

    items = (await db.execute(
        select(NotificationLog)
        .where(base_filter)
        .order_by(NotificationLog.created_at.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE)
    )).scalars().all()

    # 获取频道列表用于筛选
    channels = (await db.execute(
        select(Channel).where(Channel.user_id == user.id).order_by(Channel.name)
    )).scalars().all()

    return tpl.TemplateResponse("history/list.html", {
        "request": request, "user": user, "items": items,
        "page": page, "total_pages": total_pages, "total": total,
        "status": status, "channel_id": channel_id or "",
        "keyword": keyword,
        "channels": channels,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/{item_id}", response_class=HTMLResponse)
async def history_detail(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotificationLog)
        .where(NotificationLog.id == item_id, NotificationLog.user_id == user.id)
        .options(selectinload(NotificationLog.webhook_log))
    )).scalar_one_or_none()

    if not item:
        return RedirectResponse("/history?msg=记录不存在&msg_type=error", status_code=303)

    return tpl.TemplateResponse("history/detail.html", {
        "request": request, "user": user, "item": item,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/{item_id}/resend", response_class=JSONResponse)
async def history_resend(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """HTMX: 重新发送一条通知"""
    nlog = (await db.execute(
        select(NotificationLog)
        .where(NotificationLog.id == item_id, NotificationLog.user_id == user.id)
    )).scalar_one_or_none()
    if not nlog:
        return JSONResponse({"ok": False, "msg": "记录不存在"})

    # 查找通知配置
    ch = (await db.execute(
        select(Channel)
        .where(Channel.id == nlog.channel_id)
        .options(selectinload(Channel.notifier_config))
    )).scalar_one_or_none()

    if not ch or not ch.notifier_config:
        return JSONResponse({"ok": False, "msg": "通知渠道配置不存在"})

    config = json.loads(ch.notifier_config.config_json)
    notifier = get_notifier(ch.notifier_config.notifier_type)
    if not notifier:
        return JSONResponse({"ok": False, "msg": "通知类型不支持"})

    try:
        tpl_obj = ch.template
        body_format = tpl_obj.body_format if tpl_obj else "text"
        success = await notifier.send(
            subject=nlog.subject,
            body=nlog.body,
            body_format=body_format,
            config=config,
        )
        if success:
            nlog.status = "success"
            nlog.error_message = ""
            nlog.retry_count += 1
            await db.commit()
            return JSONResponse({"ok": True, "msg": "重发成功"})
        else:
            return JSONResponse({"ok": False, "msg": "发送失败"})
    except Exception as e:
        nlog.retry_count += 1
        nlog.error_message = str(e)[:500]
        await db.commit()
        return JSONResponse({"ok": False, "msg": f"发送失败: {str(e)}"})