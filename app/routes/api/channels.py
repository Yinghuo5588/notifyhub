"""频道 API"""
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import (
    User,
    Channel,
    NotificationTemplate,
    NotifierConfig,
    FilterRule,
    gen_token,
)

router = APIRouter(prefix="/channels", tags=["api-channels"])


class ChannelReq(BaseModel):
    name: str
    description: str = ""
    template_id: int | None = None
    notifier_config_id: int | None = None
    is_active: bool = True
    is_shared: bool = False


class FilterRuleReq(BaseModel):
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


def filter_to_item(rule: FilterRule) -> dict:
    return {
        "id": rule.id,
        "channel_id": rule.channel_id,
        "name": rule.name or "",
        "field_path": rule.field_path or "",
        "match_type": rule.match_type,
        "pattern": rule.pattern,
        "mode": rule.mode,
        "is_active": bool(rule.is_active),
        "created_at": dt_to_str(rule.created_at),
    }


def channel_to_item(ch: Channel, include_filters: bool = False) -> dict:
    data = {
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

    if include_filters:
        data["filter_rules"] = [
            filter_to_item(rule)
            for rule in getattr(ch, "filter_rules", [])
        ]

    return data


async def get_owned_channel(
    channel_id: int,
    db: AsyncSession,
    user: User,
    with_filters: bool = False,
) -> Channel:
    options = [
        selectinload(Channel.template),
        selectinload(Channel.notifier_config),
    ]
    if with_filters:
        options.append(selectinload(Channel.filter_rules))

    ch = (
        await db.execute(
            select(Channel)
            .where(Channel.id == channel_id, Channel.user_id == user.id)
            .options(*options)
        )
    ).scalar_one_or_none()

    if not ch:
        raise HTTPException(status_code=404, detail="频道不存在")

    return ch


@router.get("/form-options")
async def api_channel_form_options(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    templates = (
        await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.user_id == user.id)
            .order_by(NotificationTemplate.name)
        )
    ).scalars().all()

    notifiers = (
        await db.execute(
            select(NotifierConfig)
            .where(
                NotifierConfig.user_id == user.id,
                NotifierConfig.is_active == True,
            )
            .order_by(NotifierConfig.name)
        )
    ).scalars().all()

    return {
        "templates": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description or "",
                "body_format": item.body_format,
                "is_shared": bool(item.is_shared),
            }
            for item in templates
        ],
        "notifiers": [
            {
                "id": item.id,
                "name": item.name,
                "notifier_type": item.notifier_type,
                "is_active": bool(item.is_active),
                "is_shared": bool(item.is_shared),
            }
            for item in notifiers
        ],
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


@router.post("")
async def api_channel_create(
    payload: ChannelReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="频道名称不能为空")

    if payload.template_id:
        tpl = (
            await db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.id == payload.template_id,
                    NotificationTemplate.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if not tpl:
            raise HTTPException(status_code=400, detail="通知模板不存在")

    if payload.notifier_config_id:
        nc = (
            await db.execute(
                select(NotifierConfig).where(
                    NotifierConfig.id == payload.notifier_config_id,
                    NotifierConfig.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if not nc:
            raise HTTPException(status_code=400, detail="通知渠道不存在")

    ch = Channel(
        user_id=user.id,
        name=name,
        description=payload.description.strip(),
        template_id=payload.template_id,
        notifier_config_id=payload.notifier_config_id,
        is_active=payload.is_active,
    )

    # 仅管理员可设置共享
    if user.is_admin:
        ch.is_shared = payload.is_shared

    db.add(ch)
    await db.commit()
    await db.refresh(ch)

    ch = await get_owned_channel(ch.id, db, user, with_filters=True)

    return channel_to_item(ch, include_filters=True)


@router.get("/{channel_id}")
async def api_channel_detail(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    ch = await get_owned_channel(channel_id, db, user, with_filters=True)
    return channel_to_item(ch, include_filters=True)


@router.put("/{channel_id}")
async def api_channel_update(
    channel_id: int,
    payload: ChannelReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    ch = await get_owned_channel(channel_id, db, user, with_filters=True)

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="频道名称不能为空")

    if payload.template_id:
        tpl = (
            await db.execute(
                select(NotificationTemplate).where(
                    NotificationTemplate.id == payload.template_id,
                    NotificationTemplate.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if not tpl:
            raise HTTPException(status_code=400, detail="通知模板不存在")

    if payload.notifier_config_id:
        nc = (
            await db.execute(
                select(NotifierConfig).where(
                    NotifierConfig.id == payload.notifier_config_id,
                    NotifierConfig.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if not nc:
            raise HTTPException(status_code=400, detail="通知渠道不存在")

    ch.name = name
    ch.description = payload.description.strip()
    ch.template_id = payload.template_id
    ch.notifier_config_id = payload.notifier_config_id
    ch.is_active = payload.is_active

    if user.is_admin:
        ch.is_shared = payload.is_shared

    await db.commit()

    ch = await get_owned_channel(channel_id, db, user, with_filters=True)
    return channel_to_item(ch, include_filters=True)


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


@router.post("/{channel_id}/regenerate-token")
async def api_channel_regenerate_token(
    channel_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    ch = await get_owned_channel(channel_id, db, user, with_filters=True)
    ch.token = gen_token()
    await db.commit()

    ch = await get_owned_channel(channel_id, db, user, with_filters=True)
    return channel_to_item(ch, include_filters=True)


@router.post("/{channel_id}/filters")
async def api_channel_filter_create(
    channel_id: int,
    payload: FilterRuleReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_channel(channel_id, db, user)

    if not payload.pattern.strip():
        raise HTTPException(status_code=400, detail="匹配内容不能为空")

    if payload.match_type not in ("keyword", "regex"):
        raise HTTPException(status_code=400, detail="匹配方式不支持")

    if payload.mode not in ("whitelist", "blacklist"):
        raise HTTPException(status_code=400, detail="过滤模式不支持")

    rule = FilterRule(
        channel_id=channel_id,
        user_id=user.id,
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


@router.put("/{channel_id}/filters/{rule_id}")
async def api_channel_filter_update(
    channel_id: int,
    rule_id: int,
    payload: FilterRuleReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_channel(channel_id, db, user)

    rule = (
        await db.execute(
            select(FilterRule).where(
                FilterRule.id == rule_id,
                FilterRule.channel_id == channel_id,
                FilterRule.user_id == user.id,
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


@router.post("/{channel_id}/filters/{rule_id}/toggle")
async def api_channel_filter_toggle(
    channel_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_channel(channel_id, db, user)

    rule = (
        await db.execute(
            select(FilterRule).where(
                FilterRule.id == rule_id,
                FilterRule.channel_id == channel_id,
                FilterRule.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="过滤规则不存在")

    rule.is_active = not rule.is_active
    await db.commit()
    await db.refresh(rule)

    return filter_to_item(rule)


@router.delete("/{channel_id}/filters/{rule_id}")
async def api_channel_filter_delete(
    channel_id: int,
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    await get_owned_channel(channel_id, db, user)

    rule = (
        await db.execute(
            select(FilterRule).where(
                FilterRule.id == rule_id,
                FilterRule.channel_id == channel_id,
                FilterRule.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not rule:
        raise HTTPException(status_code=404, detail="过滤规则不存在")

    await db.delete(rule)
    await db.commit()

    return {"ok": True}