"""通知渠道 API"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, NotifierConfig
from app.notifiers.registry import get_all_notifier_types, get_notifier

router = APIRouter(prefix="/notifiers", tags=["api-notifiers"])


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def mask_config(config: dict, schema: dict) -> dict:
    """
    列表/编辑返回配置时对 password 字段脱敏。

    第三阶段列表页其实不需要完整 config，但这里先保守处理。
    """
    result = dict(config)

    for key, field in schema.items():
        if field.get("type") == "password" and key in result and result[key]:
            result[key] = "******"

    return result


def notifier_to_item(item: NotifierConfig) -> dict:
    notifier = get_notifier(item.notifier_type)
    schema = notifier.get_config_schema() if notifier else {}

    try:
        raw_config = json.loads(item.config_json or "{}")
    except Exception:
        raw_config = {}

    return {
        "id": item.id,
        "name": item.name,
        "notifier_type": item.notifier_type,
        "config": mask_config(raw_config, schema),
        "is_active": bool(item.is_active),
        "is_shared": bool(item.is_shared),
        "created_at": dt_to_str(item.created_at),
        "updated_at": dt_to_str(item.updated_at),
    }


@router.get("/types")
async def api_notifier_types(
    user: User = Depends(get_current_api_user),
):
    return get_all_notifier_types()


@router.get("")
async def api_notifier_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    rows = (
        await db.execute(
            select(NotifierConfig)
            .where(NotifierConfig.user_id == user.id)
            .order_by(NotifierConfig.created_at.desc())
        )
    ).scalars().all()

    return [notifier_to_item(item) for item in rows]


@router.delete("/{item_id}")
async def api_notifier_delete(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = (
        await db.execute(
            select(NotifierConfig).where(
                NotifierConfig.id == item_id,
                NotifierConfig.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="通知渠道不存在")

    await db.delete(item)
    await db.commit()

    return {"ok": True}


@router.post("/{item_id}/test")
async def api_notifier_test(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = (
        await db.execute(
            select(NotifierConfig).where(
                NotifierConfig.id == item_id,
                NotifierConfig.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="通知渠道不存在")

    notifier = get_notifier(item.notifier_type)
    if not notifier:
        raise HTTPException(status_code=400, detail="通知类型不支持")

    try:
        config = json.loads(item.config_json or "{}")
    except Exception:
        raise HTTPException(status_code=400, detail="通知渠道配置不是有效 JSON")

    ok, msg = await notifier.test_connection(config)

    return {
        "ok": ok,
        "msg": msg,
    }