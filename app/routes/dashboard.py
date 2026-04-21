"""仪表盘首页 —— v2 管理员/普通用户差异化展示"""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import (
    User, Channel, NotificationLog, WebhookLog,
    NotificationTemplate, NotifierConfig, ChannelSubscription,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today_start - timedelta(days=6)

    # ── 频道总数 ──
    ch_count = (await db.execute(
        select(func.count(Channel.id)).where(Channel.user_id == user.id)
    )).scalar() or 0

    # ── 模板总数 ──
    tpl_count = (await db.execute(
        select(func.count(NotificationTemplate.id)).where(NotificationTemplate.user_id == user.id)
    )).scalar() or 0

    # ── 通知渠道总数 ──
    nc_count = (await db.execute(
        select(func.count(NotifierConfig.id)).where(NotifierConfig.user_id == user.id)
    )).scalar() or 0

    # ── 管理员看系统用户数 / 普通用户看订阅数 ──
    if user.is_admin:
        extra_count = (await db.execute(
            select(func.count(User.id))
        )).scalar() or 0
    else:
        extra_count = (await db.execute(
            select(func.count(ChannelSubscription.id)).where(ChannelSubscription.user_id == user.id)
        )).scalar() or 0

    # ── 今日Webhook数 ──
    today_hooks = (await db.execute(
        select(func.count(WebhookLog.id)).where(
            WebhookLog.user_id == user.id,
            WebhookLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日发送数 ──
    today_sent = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日成功数 ──
    today_ok = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "success",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日失败数 ──
    today_fail = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "failed",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日限频数 ──
    today_limited = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "rate_limited",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 7天趋势（每天成功+失败） ──
    trend_days = []
    trend_success = []
    trend_failed = []
    for i in range(7):
        day_start = (today_start + timedelta(days=i)).replace(tzinfo=None)
        day_end = (day_start + timedelta(days=1))
        ok = (await db.execute(
            select(func.count(NotificationLog.id)).where(
                NotificationLog.user_id == user.id,
                NotificationLog.status == "success",
                NotificationLog.created_at >= day_start,
                NotificationLog.created_at < day_end,
            )
        )).scalar() or 0
        fail = (await db.execute(
            select(func.count(NotificationLog.id)).where(
                NotificationLog.user_id == user.id,
                NotificationLog.status == "failed",
                NotificationLog.created_at >= day_start,
                NotificationLog.created_at < day_end,
            )
        )).scalar() or 0
        d = day_start + timedelta(hours=8)  # 北京时间
        trend_days.append(d.strftime("%m-%d"))
        trend_success.append(ok)
        trend_failed.append(fail)

    # ── 最近5条通知 ──
    recent_result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == user.id)
        .order_by(NotificationLog.created_at.desc())
        .limit(5)
    )
    recent_logs = recent_result.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": {
            "channels": ch_count,
            "templates": tpl_count,
            "notifier_configs": nc_count,
            "extra_count": extra_count,
            "today_hooks": today_hooks,
            "today_sent": today_sent,
            "today_ok": today_ok,
            "today_fail": today_fail,
            "today_limited": today_limited,
        },
        "recent_logs": recent_logs,
        "trend_days": trend_days,
        "trend_success": trend_success,
        "trend_failed": trend_failed,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # ── 频道总数 ──
    ch_count = (await db.execute(
        select(func.count(Channel.id)).where(Channel.user_id == user.id)
    )).scalar() or 0

    # ── 模板总数 ──
    tpl_count = (await db.execute(
        select(func.count(NotificationTemplate.id)).where(NotificationTemplate.user_id == user.id)
    )).scalar() or 0

    # ── 通知渠道总数 ──
    nc_count = (await db.execute(
        select(func.count(NotifierConfig.id)).where(NotifierConfig.user_id == user.id)
    )).scalar() or 0

    # ── 管理员看系统用户数 / 普通用户看订阅数 ──
    if user.is_admin:
        extra_count = (await db.execute(
            select(func.count(User.id))
        )).scalar() or 0
    else:
        extra_count = (await db.execute(
            select(func.count(ChannelSubscription.id)).where(ChannelSubscription.user_id == user.id)
        )).scalar() or 0

    # ── 今日Webhook数 ──
    today_hooks = (await db.execute(
        select(func.count(WebhookLog.id)).where(
            WebhookLog.user_id == user.id,
            WebhookLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日发送数 ──
    today_sent = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日成功数 ──
    today_ok = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "success",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日失败数 ──
    today_fail = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "failed",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 今日限频数 ──
    today_limited = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "rate_limited",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    # ── 最近10条通知 ──
    recent_result = await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == user.id)
        .order_by(NotificationLog.created_at.desc())
        .limit(5)
    )
    recent_logs = recent_result.scalars().all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "stats": {
            "channels": ch_count,
            "templates": tpl_count,
            "notifier_configs": nc_count,
            "extra_count": extra_count,
            "today_hooks": today_hooks,
            "today_sent": today_sent,
            "today_ok": today_ok,
            "today_fail": today_fail,
            "today_limited": today_limited,
        },
        "recent_logs": recent_logs,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })