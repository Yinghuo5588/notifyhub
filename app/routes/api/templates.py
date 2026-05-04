"""模板 API"""
import json

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import (
    User,
    NotificationTemplate,
    SharedTemplateAccess,
    WebhookLog,
    Channel,
)
from app.services.template_renderer import render_template_string, extract_variables

router = APIRouter(prefix="/templates", tags=["api-templates"])


class TemplateReq(BaseModel):
    name: str
    description: str = ""
    subject_template: str = ""
    body_template: str = ""
    body_format: str = "text"
    sample_data: str = "{}"
    is_shared: bool = False


class TemplatePreviewReq(BaseModel):
    subject_template: str
    body_template: str
    sample_data: str = "{}"


class ExtractVariablesReq(BaseModel):
    sample_data: str = "{}"


def dt_to_str(value):
    if not value:
        return None
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def template_to_item(item: NotificationTemplate, include_source: bool = True) -> dict:
    data = {
        "id": item.id,
        "name": item.name,
        "description": item.description or "",
        "body_format": item.body_format,
        "is_shared": bool(item.is_shared),
        "created_at": dt_to_str(item.created_at),
        "updated_at": dt_to_str(item.updated_at),
    }

    if include_source:
        data.update(
            {
                "subject_template": item.subject_template,
                "body_template": item.body_template,
                "sample_data": item.sample_data,
            }
        )

    return data


async def get_owned_template(
    template_id: int,
    db: AsyncSession,
    user: User,
) -> NotificationTemplate:
    item = (
        await db.execute(
            select(NotificationTemplate).where(
                NotificationTemplate.id == template_id,
                NotificationTemplate.user_id == user.id,
            )
        )
    ).scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="模板不存在")

    return item


async def infer_variables_from_recent_log(
    template_id: int,
    db: AsyncSession,
    user: User,
) -> tuple[list[str], str | None]:
    """
    如果 sample_data 为空，尝试从最近关联该模板的 WebhookLog 中提取变量。
    """
    log = (
        await db.execute(
            select(WebhookLog)
            .join(Channel, Channel.id == WebhookLog.channel_id)
            .where(
                Channel.template_id == template_id,
                Channel.user_id == user.id,
            )
            .order_by(WebhookLog.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    if not log or not log.parsed_data:
        return [], None

    try:
        data = json.loads(log.parsed_data)
        return extract_variables(data), log.parsed_data
    except Exception:
        return [], None


@router.get("")
async def api_template_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    rows = (
        await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.user_id == user.id)
            .order_by(NotificationTemplate.created_at.desc())
        )
    ).scalars().all()

    return [template_to_item(item, include_source=True) for item in rows]


@router.post("")
async def api_template_create(
    payload: TemplateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="模板名称不能为空")

    if payload.body_format not in ("text", "html"):
        raise HTTPException(status_code=400, detail="正文格式不支持")

    item = NotificationTemplate(
        user_id=user.id,
        name=name,
        description=payload.description.strip(),
        subject_template=payload.subject_template,
        body_template=payload.body_template,
        body_format=payload.body_format,
        sample_data=payload.sample_data or "{}",
    )

    if user.is_admin:
        item.is_shared = payload.is_shared

    db.add(item)
    await db.commit()
    await db.refresh(item)

    return template_to_item(item, include_source=True)


@router.get("/shared")
async def api_shared_template_list(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    rows = (
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
            .order_by(NotificationTemplate.updated_at.desc())
        )
    ).scalars().all()

    # 普通用户共享模板不返回正文源码
    return [template_to_item(item, include_source=False) for item in rows]


@router.post("/preview")
async def api_template_preview(
    payload: TemplatePreviewReq,
    user: User = Depends(get_current_api_user),
):
    try:
        data = json.loads(payload.sample_data) if payload.sample_data else {}
    except Exception:
        return {
            "subject": "[JSON解析错误]",
            "body": "示例数据不是有效的 JSON",
        }

    subject = render_template_string(payload.subject_template, data)
    body = render_template_string(payload.body_template, data)

    return {
        "subject": subject,
        "body": body,
    }


@router.post("/extract-variables")
async def api_template_extract_variables(
    payload: ExtractVariablesReq,
    user: User = Depends(get_current_api_user),
):
    try:
        data = json.loads(payload.sample_data) if payload.sample_data else {}
    except Exception:
        raise HTTPException(status_code=400, detail="示例数据不是有效的 JSON")

    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="示例数据必须是 JSON 对象")

    return {
        "variables": extract_variables(data),
    }


@router.get("/{template_id}")
async def api_template_detail(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_template(template_id, db, user)

    variables: list[str] = []
    sample_from_log: str | None = None

    try:
        sample_data = json.loads(item.sample_data) if item.sample_data else {}
        if isinstance(sample_data, dict):
            variables = extract_variables(sample_data)
    except Exception:
        variables = []

    if not variables:
        variables, sample_from_log = await infer_variables_from_recent_log(
            template_id=template_id,
            db=db,
            user=user,
        )

    if sample_from_log and (not item.sample_data or item.sample_data == "{}"):
        item.sample_data = sample_from_log
        await db.commit()
        await db.refresh(item)

    data = template_to_item(item, include_source=True)
    data["variables"] = variables

    return data


@router.put("/{template_id}")
async def api_template_update(
    template_id: int,
    payload: TemplateReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_template(template_id, db, user)

    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="模板名称不能为空")

    if payload.body_format not in ("text", "html"):
        raise HTTPException(status_code=400, detail="正文格式不支持")

    item.name = name
    item.description = payload.description.strip()
    item.subject_template = payload.subject_template
    item.body_template = payload.body_template
    item.body_format = payload.body_format
    item.sample_data = payload.sample_data or "{}"

    if user.is_admin:
        item.is_shared = payload.is_shared

    await db.commit()
    await db.refresh(item)

    return template_to_item(item, include_source=True)


@router.delete("/{template_id}")
async def api_template_delete(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
    item = await get_owned_template(template_id, db, user)

    await db.delete(item)
    await db.commit()

    return {"ok": True}