"""通知渠道配置管理（邮箱等）—— v2 支持共享标记"""
import json
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import User, NotifierConfig
from app.notifiers.registry import get_notifier, get_all_notifier_types

router = APIRouter(prefix="/notifiers")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def notifier_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(NotifierConfig)
        .where(NotifierConfig.user_id == user.id)
        .order_by(NotifierConfig.created_at.desc())
    )
    items = result.scalars().all()
    return tpl.TemplateResponse("notifiers/list.html", {
        "request": request, "user": user, "items": items,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/new", response_class=HTMLResponse)
async def notifier_new(
    request: Request,
    user: User = Depends(get_current_user),
):
    types = get_all_notifier_types()
    return tpl.TemplateResponse("notifiers/form.html", {
        "request": request, "user": user, "item": None,
        "notifier_types": types, "config_values": {},
    })


@router.post("/new")
async def notifier_create(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    form = await request.form()
    name = form.get("name", "")
    notifier_type = form.get("notifier_type", "email")

    notifier = get_notifier(notifier_type)
    schema = notifier.get_config_schema() if notifier else {}
    config = {}
    for key in schema:
        val = form.get(f"config_{key}", "")
        if schema[key]["type"] == "checkbox":
            val = f"config_{key}" in form.keys()
        config[key] = val

    item = NotifierConfig(
        user_id=user.id,
        name=name,
        notifier_type=notifier_type,
        config_json=json.dumps(config, ensure_ascii=False),
    )
    # 仅管理员可设置共享
    if user.is_admin:
        item.is_shared = "is_shared" in form
    db.add(item)
    await db.commit()
    return RedirectResponse(f"/notifiers/{item.id}/edit?msg=创建成功&msg_type=success", status_code=303)


@router.get("/{item_id}/edit", response_class=HTMLResponse)
async def notifier_edit(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotifierConfig)
        .where(NotifierConfig.id == item_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/notifiers?msg=不存在&msg_type=error", status_code=303)

    types = get_all_notifier_types()
    config_values = {}
    try:
        config_values = json.loads(item.config_json)
    except Exception:
        pass

    return tpl.TemplateResponse("notifiers/form.html", {
        "request": request, "user": user, "item": item,
        "notifier_types": types, "config_values": config_values,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/{item_id}/edit")
async def notifier_update(
    item_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotifierConfig)
        .where(NotifierConfig.id == item_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return RedirectResponse("/notifiers?msg=不存在&msg_type=error", status_code=303)

    form = await request.form()
    item.name = form.get("name", item.name)

    notifier = get_notifier(item.notifier_type)
    schema = notifier.get_config_schema() if notifier else {}
    config = {}
    for key in schema:
        val = form.get(f"config_{key}", "")
        if schema[key]["type"] == "checkbox":
            val = f"config_{key}" in form.keys()
        config[key] = val

    item.config_json = json.dumps(config, ensure_ascii=False)
    item.is_active = "is_active" in form.keys()

    if user.is_admin:
        item.is_shared = "is_shared" in form.keys()

    await db.commit()
    return RedirectResponse(f"/notifiers/{item.id}/edit?msg=保存成功&msg_type=success", status_code=303)


@router.post("/{item_id}/test", response_class=JSONResponse)
async def notifier_test(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotifierConfig)
        .where(NotifierConfig.id == item_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if not item:
        return JSONResponse({"ok": False, "msg": "配置不存在"})

    notifier = get_notifier(item.notifier_type)
    if not notifier:
        return JSONResponse({"ok": False, "msg": "通知类型不支持"})

    config = json.loads(item.config_json)
    ok, msg = await notifier.test_connection(config)
    return JSONResponse({"ok": ok, "msg": msg})


@router.post("/{item_id}/delete")
async def notifier_delete(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    item = (await db.execute(
        select(NotifierConfig)
        .where(NotifierConfig.id == item_id, NotifierConfig.user_id == user.id)
    )).scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.commit()
    return RedirectResponse("/notifiers?msg=已删除&msg_type=success", status_code=303)