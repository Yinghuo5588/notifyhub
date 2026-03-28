"""通知模板管理"""
import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, NotificationTemplate, WebhookLog, Channel, SharedTemplateAccess
from app.services.template_renderer import render_template_string, extract_variables

router = APIRouter(prefix="/templates")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def template_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.user_id == user.id)
        .order_by(NotificationTemplate.created_at.desc())
    )
    items = result.scalars().all()
    return tpl.TemplateResponse("msg_tpl/list.html", {
        "request": request, "user": user, "items": items,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/shared", response_class=HTMLResponse)
async def shared_template_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (await db.execute(
        select(NotificationTemplate)
        .join(SharedTemplateAccess, SharedTemplateAccess.template_id == NotificationTemplate.id)
        .where(SharedTemplateAccess.user_id == user.id, NotificationTemplate.is_shared == True)
        .order_by(NotificationTemplate.updated_at.desc())
    )).scalars().all()
    return tpl.TemplateResponse("msg_tpl/shared_list.html", {
        "request": request, "user": user, "items": rows,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/new", response_class=HTMLResponse)
async def template_new(
    request: Request,
    user: User = Depends(get_current_user),
):
    return tpl.TemplateResponse("msg_tpl/form.html", {
        "request": request, "user": user, "item": None, "variables": [],
    })


@router.post("/new")
async def template_create(
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    subject_template: str = Form(""),
    body_template: str = Form(""),
    body_format: str = Form("text"),
    sample_data: str = Form("{}"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = NotificationTemplate(
        user_id=user.id,
        name=name,
        description=description,
        subject_template=subject_template,
        body_template=body_template,
        body_format=body_format,
        sample_data=sample_data,
    )
    if user.is_admin:
        form = await request.form()
        item.is_shared = "is_shared" in form
    db.add(item)
    await db.commit()
    return RedirectResponse(f"/templates/{item.id}/edit?msg=模板创建成功&msg_type=success", status_code=303)


@router.get("/{item_id}/edit", response_class=HTMLResponse)
async def template_edit(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.id == item_id, NotificationTemplate.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/templates?msg=模板不存在&msg_type=error", status_code=303)

    variables = []
    try:
        data = json.loads(item.sample_data) if item.sample_data else {}
        if data:
            variables = extract_variables(data)
    except Exception:
        pass

    if not variables:
        result = await db.execute(
            select(WebhookLog)
            .join(Channel, Channel.id == WebhookLog.channel_id)
            .where(
                Channel.template_id == item.id,
                Channel.user_id == user.id,
            )
            .order_by(WebhookLog.created_at.desc())
            .limit(1)
        )
        log = result.scalar_one_or_none()
        if log and log.parsed_data:
            try:
                data = json.loads(log.parsed_data)
                variables = extract_variables(data)
                if not item.sample_data or item.sample_data == "{}":
                    item.sample_data = log.parsed_data
                    await db.commit()
            except Exception:
                pass

    return tpl.TemplateResponse("msg_tpl/form.html", {
        "request": request, "user": user, "item": item,
        "variables": variables,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/{item_id}/edit")
async def template_update(
    item_id: int,
    request: Request,
    name: str = Form(...),
    description: str = Form(""),
    subject_template: str = Form(""),
    body_template: str = Form(""),
    body_format: str = Form("text"),
    sample_data: str = Form("{}"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.id == item_id, NotificationTemplate.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/templates?msg=模板不存在&msg_type=error", status_code=303)

    item.name = name
    item.description = description
    item.subject_template = subject_template
    item.body_template = body_template
    item.body_format = body_format
    item.sample_data = sample_data
    if user.is_admin:
        form = await request.form()
        item.is_shared = "is_shared" in form
    await db.commit()
    return RedirectResponse(f"/templates/{item.id}/edit?msg=保存成功&msg_type=success", status_code=303)


@router.post("/{item_id}/delete")
async def template_delete(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotificationTemplate)
        .where(NotificationTemplate.id == item_id, NotificationTemplate.user_id == user.id)
    )).scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return RedirectResponse("/templates?msg=模板已删除&msg_type=success", status_code=303)


@router.post("/preview", response_class=JSONResponse)
async def template_preview(
    request: Request,
    user: User = Depends(get_current_user),
):
    body = await request.json()
    subject_tpl = body.get("subject_template", "")
    body_tpl = body.get("body_template", "")
    sample = body.get("sample_data", "{}")

    try:
        data = json.loads(sample) if sample else {}
    except Exception:
        return JSONResponse({"subject": "[JSON解析错误]", "body": "示例数据不是有效的JSON"})

    subject = render_template_string(subject_tpl, data)
    rendered_body = render_template_string(body_tpl, data)
    return JSONResponse({"subject": subject, "body": rendered_body})
