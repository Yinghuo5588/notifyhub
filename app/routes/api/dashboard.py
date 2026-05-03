"""仪表盘 API"""
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import (
    User, Channel, NotificationLog, WebhookLog,
    NotificationTemplate, NotifierConfig, ChannelSubscription,
)

router = APIRouter(prefix="/dashboard", tags=["api-dashboard"])


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


@router.get("")
async def api_dashboard(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    ch_count = (await db.execute(
        select(func.count(Channel.id)).where(Channel.user_id == user.id)
    )).scalar() or 0

    tpl_count = (await db.execute(
        select(func.count(NotificationTemplate.id)).where(
            NotificationTemplate.user_id == user.id
        )
    )).scalar() or 0

    nc_count = (await db.execute(
        select(func.count(NotifierConfig.id)).where(
            NotifierConfig.user_id == user.id
        )
    )).scalar() or 0

    if user.is_admin:
        extra_count = (await db.execute(
            select(func.count(User.id))
        )).scalar() or 0
    else:
        extra_count = (await db.execute(
            select(func.count(ChannelSubscription.id)).where(
                ChannelSubscription.user_id == user.id
            )
        )).scalar() or 0

    today_hooks = (await db.execute(
        select(func.count(WebhookLog.id)).where(
            WebhookLog.user_id == user.id,
            WebhookLog.created_at >= today_start,
        )
    )).scalar() or 0

    today_sent = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    today_ok = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "success",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    today_fail = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "failed",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    today_limited = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.user_id == user.id,
            NotificationLog.status == "rate_limited",
            NotificationLog.created_at >= today_start,
        )
    )).scalar() or 0

    trend_days = []
    trend_success = []
    trend_failed = []

    for i in range(7):
        day_start = today_start - timedelta(days=6 - i)
        day_end = day_start + timedelta(days=1)

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

        display_day = day_start + timedelta(hours=8)
        trend_days.append(display_day.strftime("%m-%d"))
        trend_success.append(ok)
        trend_failed.append(fail)

    recent_logs = (await db.execute(
        select(NotificationLog)
        .where(NotificationLog.user_id == user.id)
        .order_by(NotificationLog.created_at.desc())
        .limit(5)
    )).scalars().all()

    return {
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
        "recent_logs": [
            {
                "id": item.id,
                "channel_id": item.channel_id,
                "notifier_type": item.notifier_type,
                "subject": item.subject,
                "body": item.body,
                "status": item.status,
                "error_message": item.error_message,
                "retry_count": item.retry_count,
                "created_at": dt_to_str(item.created_at),
            }
            for item in recent_logs
        ],
        "trend": {
            "days": trend_days,
            "success": trend_success,
            "failed": trend_failed,
        },
    }