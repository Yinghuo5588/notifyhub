"""共享订阅 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import (
    User,
    ChannelSubscription,
    SubscriptionFilter,
    NotificationTemplate,
    NotifierConfig,
    SharedTemplateAccess,
    SharedNotifierAccess,
)

router = APIRouter(prefix="/subscriptions", tags=["api-subscriptions"])


class SubscriptionUpdateReq(BaseModel):
    template_id: int | None = None
    notifier_config_id: int | None = None
    custom_recipients: str = ""
    is_active: bool = False


class SubscriptionFilterReq(BaseModel):
    name: str = ""
    field_path: str = ""
    match_type: str = "keyword"
    pattern: str
    mode: str = "blacklist"
    is_active: bool = True


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def filter_to_item(rule: SubscriptionFilter) -> dict:
    return {
        "id": rule.id,
        "subscription_id": rule.subscription_id,
        "name": rule.name or "",
        "field_path": rule.field_path or "",
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "mode": rule.mode,
        "is_active": bool(rule.is_active),
        "created_at": dt_to_str(rule.created_at),
    }


def sub_to_item(sub: ChannelSubscription, include_filters: bool = False) -> dict:
    data = {
        "id": sub.id,
        "channel_id": sub.channel_id,
        "channel_name": sub.channel.name if sub.channel else "",
        "channel_description": sub.channel.description if sub.channel else "",
        "template_id": sub.template_id,
        "template_name": sub.template.name if sub.template else "",
        "notifier_config_id": sub.notifier_config_id,
        "notifier_name": sub.notifier_config.name if sub.notifier_config else "",
        "notifier_type": sub.notifier_config.notifier_type if sub.notifier_config else "",
        "custom_recipients": sub.custom_recipients or "",
        "is_active": bool(sub.is_active),
        "sends_today": sub.sends_today or 0,
        "sends_this_hour": sub.sends_this_hour or 0,
        "last_send_at": dt_to_str(sub.last_send_at),
        "hour_reset_at": dt_to_str(sub.hour_reset_at),
        "day_reset_at": dt_to_str(sub.day_reset_at),
        "created_at": dt_to_str(sub.created_at),
        "limits": None,
    }

    if sub.channel:
        data["limits"] = {
            "per_hour_limit": sub.channel.per_hour_limit,
            "per_day_limit": sub.channel.per_day_limit,
            "min_interval": sub.channel.min_interval,
            "global_hour_limit": sub.channel.global_hour_limit,
            "global_day_limit": sub.channel.global_day_limit,
        }

    if include_filters:
        data["filters"] = [filter_to_item(rule) for rule in getattr(sub, "filters", [])]

    return data


async def get_owned_subscription(
    sub_id: int,
    db: AsyncSession,
    user: User,
    with_filters: bool = False,
) -> ChannelSubscription:
    options = [
        selectinload(ChannelSubscription.channel),
        selectinload(ChannelSubscription.template),
        selectinload(ChannelSubscription.notifier_config),
    ]

    if with_filters:
        options.append(selectinload(ChannelSubscription.filters))

    sub = (
        await db.execute(
            select(ChannelSubscription)
            .where(
                ChannelSubscription.id == sub_id,
                ChannelSubscription.user_id == user.id,
            )
            .options(*options)
        )
    ).scalar_one_or_none()

    if not sub:
        raise HTTPException(status_code=404, detail="订阅不存在")

    return sub


async def can_use_template(
    template_id: int,
    db: AsyncSession,
    user: User,
) -> bool:
    tpl = (
        await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )
    ).scalar_one_or_none()

    if not tpl:
        return False

    if tpl.user_id == user.id:
        return True

    access = (
        await db.execute(
            select(SharedTemplateAccess).where(
                SharedTemplateAccess.template_id == template_id,
                SharedTemplateAccess.user_id == user.id,
            )
            .join(
                NotificationTemplate,
                NotificationTemplate.id == SharedTemplateAccess.template_id,
            )
        )
    ).scalar_one_or_none()

    return access is not None


async def can_use_notifier(
    notifier_id: int,
    db: AsyncSession,
    user: User,
) -> bool:
    nc = (
        await db.execute(
            select(NotifierConfig).where(NotifierConfig.id == notifier_id)
        )
    ).scalar_one_or_none()

    if not nc:
        return False

    if nc.user_id == user.id:
        return True

    access = (
        await db.execute(
            select(SharedNotifierAccess).where(
                SharedNotifierAccess.notifier_config_id == notifier_id,
                SharedNotifierAccess.user_id == user.id,
            )
            .join(
                NotifierConfig,
                NotifierConfig.id == SharedNotifierAccess.notifier_config_id,
            )
        )
    ).scalar_one_or_none()

    return access is not None


@router.get("")
async def api_subscription_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    rows = (
        await db.execute(
            select(ChannelSubscription)
            .where(ChannelSubscription.user_id == user.id)
            .options(
                selectinload(ChannelSubscription.channel),
                selectinload(ChannelSubscription.template),
                selectinload(ChannelSubscription.notifier_config),
            )
            .order_by(ChannelSubscription.created_at.desc())
        )
    ).scalars().all()

    return [sub_to_item(item) for item in rows]


@router.get("/{sub_id}")
async def api_subscription_detail(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    sub = await get_owned_subscription(sub_id, db, user, with_filters=True)
    return sub_to_item(sub, include_filters=True)


@router.get("/{sub_id}/form-options")
async def api_subscription_form_options(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_subscription(sub_id, db, user)

    my_templates = (
        await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.user_id == user.id)
            .order_by(NotificationTemplate.name)
        )
    ).scalars().all()

    shared_templates = (
        await db.execute(
            select(NotificationTemplate)
            .join(
                SharedTemplateAccess,
                SharedTemplateAccess.template_id == NotificationTemplate.id,
            )
            .where(
                SharedTemplateAccess.user_id == user.id,
                NotificationTemplate.is_shared == True,
            )
            .order_by(NotificationTemplate.name)
        )
    ).scalars().all()

    my_notifiers = (
        await db.execute(
            select(NotifierConfig)
            .where(
                NotifierConfig.user_id == user.id,
                NotifierConfig.is_active == True,
            )
            .order_by(NotifierConfig.name)
        )
    ).scalars().all()

    shared_notifiers = (
        await db.execute(
            select(NotifierConfig)
            .join(
                SharedNotifierAccess,
                SharedNotifierAccess.notifier_config_id == NotifierConfig.id,
            )
            .where(
                SharedNotifierAccess.user_id == user.id,
                NotifierConfig.is_shared == True,
                NotifierConfig.is_active == True,
            )
            .order_by(NotifierConfig.name)
        )
    ).scalars().all()

    return {
        "my_templates": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description or "",
                "body_format": item.body_format,
                "is_shared": False,
            }
            for item in my_templates
        ],
        "shared_templates": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description or "",
                "body_format": item.body_format,
                "is_shared": True,
            }
            for item in shared_templates
        ],
        "my_notifiers": [
            {
                "id": item.id,
                "name": item.name,
                "notifier_type": item.notifier_type,
                "is_shared": False,
            }
            for item in my_notifiers
        ],
        "shared_notifiers": [
            {
                "id": item.id,
                "name": item.name,
                "notifier_type": item.notifier_type,
                "is_shared": True,
            }
            for item in shared_notifiers
        ],
    }


@router.put("/{sub_id}")
async def api_subscription_update(
    sub_id: int,
    payload: SubscriptionUpdateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    sub = await get_owned_subscription(sub_id, db, user, with_filters=True)

    if payload.template_id:
        allowed = await can_use_template(payload.template_id, db, user)
        if not allowed:
            raise HTTPException(status_code=400, detail="无权使用该模板")

    shared_notifier = None
    if payload.notifier_config_id:
        allowed = await can_use_notifier(payload.notifier_config_id, db, user)
        if not allowed:
            raise HTTPException(status_code=400, detail="无权使用该通知渠道")

        shared_notifier = (
            await db.execute(
                select(NotifierConfig).where(NotifierConfig.id == payload.notifier_config_id)
            )
        ).scalar_one_or_none()

    if (
        payload.is_active
        and shared_notifier
        and shared_notifier.is_shared
        and not payload.custom_recipients.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="使用共享通知渠道时必须填写收件人",
        )

    sub.template_id = payload.template_id
    sub.notifier_config_id = payload.notifier_config_id
    sub.custom_recipients = payload.custom_recipients.strip()
    sub.is_active = payload.is_active

    await db.commit()

    sub = await get_owned_subscription(sub_id, db, user, with_filters=True)
    return sub_to_item(sub, include_filters=True)


@router.post("/{sub_id}/toggle")
async def api_subscription_toggle(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    sub = await get_owned_subscription(sub_id, db, user, with_filters=True)
    sub.is_active = not sub.is_active
    await db.commit()

    sub = await get_owned_subscription(sub_id, db, user, with_filters=True)
    return sub_to_item(sub, include_filters=True)


@router.post("/{sub_id}/filters")
async def api_subscription_filter_create(
    sub_id: int,
    payload: SubscriptionFilterReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_subscription(sub_id, db, user)

    if not payload.pattern.strip():
        raise HTTPException(status_code=400, detail="匹配内容不能为空")

    if payload.match_type not in ("keyword", "regex"):
        raise HTTPException(status_code=400, detail="匹配方式不支持")

    if payload.mode not in ("whitelist", "blacklist"):
        raise HTTPException(status_code=400, detail="过滤模式不支持")

    rule = SubscriptionFilter(
        subscription_id=sub_id,
        name=payload.name.strip(),
        field_path=payload.field_path.strip(),
        match_type=payload.match_type,
        pattern=payload.pattern.strip(),
        mode=payload.mode,
        is_active=payload.is_active,
    )

    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    return filter_to_item(rule)


@router.put("/{sub_id}/filters/{rule_id}")
async def api_subscription_filter_update(
    sub_id: int,
    rule_id: int,
    payload: SubscriptionFilterReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_subscription(sub_id, db, user)

    rule = (
        await db.execute(
            select(SubscriptionFilter)
            .join(
                ChannelSubscription,
                ChannelSubscription.id == SubscriptionFilter.subscription_id,
            )
            .where(
                SubscriptionFilter.id == rule_id,
                SubscriptionFilter.subscription_id == sub_id,
                ChannelSubscription.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="过滤规则不存在")

    if not payload.pattern.strip():
        raise HTTPException(status_code=400, detail="匹配内容不能为空")

    rule.name = payload.name.strip()
    rule.field_path = payload.field_path.strip()
    rule.match_type = payload.match_type
    rule.pattern = payload.pattern.strip()
    rule.mode = payload.mode
    rule.is_active = payload.is_active

    await db.commit()
    await db.refresh(rule)

    return filter_to_item(rule)


@router.post("/{sub_id}/filters/{rule_id}/toggle")
async def api_subscription_filter_toggle(
    sub_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_subscription(sub_id, db, user)

    rule = (
        await db.execute(
            select(SubscriptionFilter)
            .join(
                ChannelSubscription,
                ChannelSubscription.id == SubscriptionFilter.subscription_id,
            )
            .where(
                SubscriptionFilter.id == rule_id,
                SubscriptionFilter.subscription_id == sub_id,
                ChannelSubscription.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="过滤规则不存在")

    rule.is_active = not rule.is_active
    await db.commit()
    await db.refresh(rule)

    return filter_to_item(rule)


@router.delete("/{sub_id}/filters/{rule_id}")
async def api_subscription_filter_delete(
    sub_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_subscription(sub_id, db, user)

    rule = (
        await db.execute(
            select(SubscriptionFilter)
            .join(
                ChannelSubscription,
                ChannelSubscription.id == SubscriptionFilter.subscription_id,
            )
            .where(
                SubscriptionFilter.id == rule_id,
                SubscriptionFilter.subscription_id == sub_id,
                ChannelSubscription.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="过滤规则不存在")

    await db.delete(rule)
    await db.commit()

    return {"ok": True}