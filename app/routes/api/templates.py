"""模板 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.dependencies import get_current_api_user
from app.models.models import User, NotificationTemplate, SharedTemplateAccess

router = APIRouter(prefix="/templates", tags=["api-templates"])


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

    # 普通用户共享模板只返回标题、描述、格式等简略信息，不暴露正文源码
    return [template_to_item(item, include_source=False) for item in rows]


@router.delete("/{template_id}")
async def api_template_delete(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_api_user),
):
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

    await db.delete(item)
    await db.commit()

    return {"ok": True}