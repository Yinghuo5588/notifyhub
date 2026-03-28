"""限频服务 —— 控制共享频道每用户/全局发送频率"""
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import ChannelSubscription, Channel, NotificationLog


def check_user_rate_limit(sub: ChannelSubscription, channel: Channel) -> tuple[bool, str]:
    """
    检查单用户限频（不查库，基于订阅记录上的计数器）
    返回 (通过与否, 原因)
    """
    now = datetime.now(timezone.utc)

    # ── 重置小时计数 ──
    if sub.hour_reset_at is None or now >= sub.hour_reset_at:
        sub.sends_this_hour = 0
        sub.hour_reset_at = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)

    # ── 重置日计数 ──
    if sub.day_reset_at is None or now >= sub.day_reset_at:
        sub.sends_today = 0
        sub.day_reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    # ── 最小间隔 ──
    if sub.last_send_at and channel.min_interval > 0:
        elapsed = (now - sub.last_send_at).total_seconds()
        if elapsed < channel.min_interval:
            return False, f"发送间隔不足（需等待 {int(channel.min_interval - elapsed)} 秒）"

    # ── 小时上限 ──
    if sub.sends_this_hour >= channel.per_hour_limit:
        return False, f"已达每小时上限 {channel.per_hour_limit} 封"

    # ── 每日上限 ──
    if sub.sends_today >= channel.per_day_limit:
        return False, f"已达每日上限 {channel.per_day_limit} 封"

    return True, "ok"


def increment_counters(sub: ChannelSubscription):
    """发送成功后更新计数器"""
    now = datetime.now(timezone.utc)
    sub.sends_this_hour += 1
    sub.sends_today += 1
    sub.last_send_at = now


async def check_global_rate_limit(
    db: AsyncSession, channel: Channel
) -> tuple[bool, str]:
    """
    检查频道全局限频（所有用户合计，需查库）
    """
    now = datetime.now(timezone.utc)
    hour_ago = now - timedelta(hours=1)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    hourly = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.channel_id == channel.id,
            NotificationLog.created_at >= hour_ago,
            NotificationLog.status.in_(["success", "pending"]),
        )
    )).scalar() or 0

    if hourly >= channel.global_hour_limit:
        return False, f"频道全局每小时上限 {channel.global_hour_limit} 封已满"

    daily = (await db.execute(
        select(func.count(NotificationLog.id)).where(
            NotificationLog.channel_id == channel.id,
            NotificationLog.created_at >= day_start,
            NotificationLog.status.in_(["success", "pending"]),
        )
    )).scalar() or 0

    if daily >= channel.global_day_limit:
        return False, f"频道全局每日上限 {channel.global_day_limit} 封已满"

    return True, "ok"