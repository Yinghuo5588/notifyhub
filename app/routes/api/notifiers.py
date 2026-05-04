"""通知渠道 API"""
import json

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, NotifierConfig
from app.notifiers.registry import get_all_notifier_types, get_notifier

router = APIRouter(prefix="/notifiers", tags=["api-notifiers"])

MASK_VALUE = "******"


class NotifierCreateReq(BaseModel):
    name: str
    notifier_type: str
    config: dict
    is_shared: bool = False


class NotifierUpdateReq(BaseModel):
    name: str
    config: dict
    is_active: bool = True
    is_shared: bool = False


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def get_schema(notifier_type: str) -> dict:
    notifier = get_notifier(notifier_type)
    return notifier.get_config_schema() if notifier else {}


def mask_config(config: dict, schema: dict) -> dict:
    result = dict(config)

    for key, field in schema.items():
        if field.get("type") == "password" and result.get(key):
            result[key] = MASK_VALUE

    return result


def merge_masked_config(old_config: dict, new_config: dict, schema: dict) -> dict:
    """
    编辑保存时，如果 password 字段仍是 ******，则保留旧值。
    """
    merged = dict(new_config)

    for key, field in schema.items():
        if field.get("type") == "password" and merged.get(key) == MASK_VALUE:
            merged[key] = old_config.get(key, "")

    return merged


def notifier_to_item(item: NotifierConfig, include_config: bool = True) -> dict:
    schema = get_schema(item.notifier_type)

    try:
        raw_config = json.loads(item.config_json or "{}")
    except Exception:
        raw_config = {}

    data = {
        "id": item.id,
        "name": item.name,
        "notifier_type": item.notifier_type,
        "is_active": bool(item.is_active),
        "is_shared": bool(item.is_shared),
        "created_at": dt_to_str(item.created_at),
        "updated_at": dt_to_str(item.updated_at),
    }

    if include_config:
        data["config"] = mask_config(raw_config, schema)

    return data


async def get_owned_notifier(
    item_id: int,
    db: AsyncSession,
    user: User,
) -> NotifierConfig:
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

    return item


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

    return [notifier_to_item(item, include_config=False) for item in rows]


@router.post("")
async def api_notifier_create(
    payload: NotifierCreateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="配置名称不能为空")

    notifier = get_notifier(payload.notifier_type)
    if not notifier:
        raise HTTPException(status_code=400, detail="通知类型不支持")

    schema = notifier.get_config_schema()
    config = dict(payload.config or {})

    for key, field in schema.items():
        if field.get("required") and not config.get(key):
            raise HTTPException(status_code=400, detail=f"{field.get('label', key)}不能为空")

    item = NotifierConfig(
        user_id=user.id,
        name=name,
        notifier_type=payload.notifier_type,
        config_json=json.dumps(config, ensure_ascii=False),
        is_active=True,
    )

    if user.is_admin:
        item.is_shared = payload.is_shared

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return notifier_to_item(item, include_config=True)


@router.get("/{item_id}")
async def api_notifier_detail(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_notifier(item_id, db, user)
    return notifier_to_item(item, include_config=True)


@router.put("/{item_id}")
async def api_notifier_update(
    item_id: int,
    payload: NotifierUpdateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_notifier(item_id, db, user)

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="配置名称不能为空")

    notifier = get_notifier(item.notifier_type)
    if not notifier:
        raise HTTPException(status_code=400, detail="通知类型不支持")

    schema = notifier.get_config_schema()

    try:
        old_config = json.loads(item.config_json or "{}")
    except Exception:
        old_config = {}

    new_config = merge_masked_config(old_config, dict(payload.config or {}), schema)

    for key, field in schema.items():
        if field.get("required") and not new_config.get(key):
            raise HTTPException(status_code=400, detail=f"{field.get('label', key)}不能为空")

    item.name = name
    item.config_json = json.dumps(new_config, ensure_ascii=False)
    item.is_active = payload.is_active

    if user.is_admin:
        item.is_shared = payload.is_shared

    await db.commit()
    await db.refresh(item)

    return notifier_to_item(item, include_config=True)


@router.delete("/{item_id}")
async def api_notifier_delete(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_notifier(item_id, db, user)

    await db.delete(item)
    await db.commit()

    return {"ok": True}


@router.post("/{item_id}/test")
async def api_notifier_test(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_notifier(item_id, db, user)

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