"""用户共享订阅管理"""
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import TEMPLATES_DIR
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.models import (
    User, Channel, ChannelSubscription, SubscriptionFilter,
    NotificationTemplate, NotifierConfig, SharedNotifierAccess, SharedTemplateAccess,
)

router = APIRouter(prefix="/subscriptions")
tpl = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
async def subscription_list(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    subs = (await db.execute(
        select(ChannelSubscription)
        .where(ChannelSubscription.user_id == user.id)
        .options(
            selectinload(ChannelSubscription.channel),
            selectinload(ChannelSubscription.template),
            selectinload(ChannelSubscription.notifier_config),
        )
        .order_by(ChannelSubscription.created_at.desc())
    )).scalars().all()

    return tpl.TemplateResponse("subscriptions/list.html", {
        "request": request, "user": user, "subscriptions": subs,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.get("/{sub_id}/edit", response_class=HTMLResponse)
async def subscription_edit(
    sub_id: int, request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = (await db.execute(
        select(ChannelSubscription)
        .where(ChannelSubscription.id == sub_id, ChannelSubscription.user_id == user.id)
        .options(
            selectinload(ChannelSubscription.channel),
            selectinload(ChannelSubscription.filters),
        )
    )).scalar_one_or_none()
    if not sub:
        return RedirectResponse("/subscriptions?msg=订阅不存在&msg_type=error", status_code=303)

    my_tpls = (await db.execute(
        select(NotificationTemplate).where(NotificationTemplate.user_id == user.id)
    )).scalars().all()

    shared_tpl_ids = (await db.execute(
        select(SharedTemplateAccess.template_id)
        .where(SharedTemplateAccess.user_id == user.id)
    )).scalars().all()
    shared_tpls = []
    if shared_tpl_ids:
        shared_tpls = (await db.execute(
            select(NotificationTemplate)
            .where(NotificationTemplate.id.in_(shared_tpl_ids), NotificationTemplate.is_shared == True)
        )).scalars().all()

    my_ncs = (await db.execute(
        select(NotifierConfig).where(NotifierConfig.user_id == user.id, NotifierConfig.is_active == True)
    )).scalars().all()

    shared_nc_ids = (await db.execute(
        select(SharedNotifierAccess.notifier_config_id)
        .where(SharedNotifierAccess.user_id == user.id)
    )).scalars().all()

    shared_ncs = []
    if shared_nc_ids:
        shared_ncs = (await db.execute(
            select(NotifierConfig)
            .where(NotifierConfig.id.in_(shared_nc_ids), NotifierConfig.is_active == True)
        )).scalars().all()

    return tpl.TemplateResponse("subscriptions/form.html", {
        "request": request, "user": user, "sub": sub,
        "my_templates": my_tpls, "shared_templates": shared_tpls,
        "my_notifiers": my_ncs, "shared_notifiers": shared_ncs,
        "filter_rules": sub.filters,
        "msg": request.query_params.get("msg", ""),
        "msg_type": request.query_params.get("msg_type", ""),
    })


@router.post("/{sub_id}/edit")
async def subscription_update(
    sub_id: int,
    template_id: int = Form(None),
    notifier_config_id: int = Form(None),
    custom_recipients: str = Form(""),
    is_active: bool = Form(False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = (await db.execute(
        select(ChannelSubscription)
        .where(ChannelSubscription.id == sub_id, ChannelSubscription.user_id == user.id)
    )).scalar_one_or_none()
    if not sub:
        return RedirectResponse("/subscriptions?msg=订阅不存在&msg_type=error", status_code=303)

    if template_id:
        tpl_item = (await db.execute(
            select(NotificationTemplate).where(NotificationTemplate.id == template_id)
        )).scalar_one_or_none()
        if not tpl_item:
            return RedirectResponse(f"/subscriptions/{sub_id}/edit?msg=模板不存在&msg_type=error", status_code=303)
        allowed = tpl_item.user_id == user.id
        if not allowed:
            allowed = (await db.execute(
                select(SharedTemplateAccess).where(
                    SharedTemplateAccess.template_id == template_id,
                    SharedTemplateAccess.user_id == user.id,
                )
            )).scalar_one_or_none() is not None
        if not allowed:
            return RedirectResponse(f"/subscriptions/{sub_id}/edit?msg=无权使用该共享模板&msg_type=error", status_code=303)

    sub.template_id = template_id if template_id else None
    sub.notifier_config_id = notifier_config_id if notifier_config_id else None
    sub.custom_recipients = custom_recipients.strip()
    sub.is_active = is_active

    if sub.notifier_config_id and sub.is_active:
        nc = (await db.execute(
            select(NotifierConfig).where(NotifierConfig.id == sub.notifier_config_id)
        )).scalar_one_or_none()
        if nc and nc.is_shared and not sub.custom_recipients:
            return RedirectResponse(
                f"/subscriptions/{sub_id}/edit?msg=使用共享通知渠道时必须填写收件人&msg_type=error",
                status_code=303
            )

    await db.commit()
    return RedirectResponse(f"/subscriptions/{sub_id}/edit?msg=保存成功&msg_type=success", status_code=303)


@router.post("/{sub_id}/toggle")
async def subscription_toggle(
    sub_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = (await db.execute(
        select(ChannelSubscription)
        .where(ChannelSubscription.id == sub_id, ChannelSubscription.user_id == user.id)
    )).scalar_one_or_none()
    if sub:
        sub.is_active = not sub.is_active
        await db.commit()
    return RedirectResponse(f"/subscriptions?msg=已{'启用' if sub.is_active else '暂停'}&msg_type=success", status_code=303)


@router.post("/filters/add")
async def sub_filter_add(
    subscription_id: int = Form(...),
    name: str = Form(""),
    field_path: str = Form(""),
    match_type: str = Form("keyword"),
    pattern: str = Form(...),
    mode: str = Form("blacklist"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sub = (await db.execute(
        select(ChannelSubscription)
        .where(ChannelSubscription.id == subscription_id, ChannelSubscription.user_id == user.id)
    )).scalar_one_or_none()
    if not sub:
        return RedirectResponse("/subscriptions?msg=订阅不存在&msg_type=error", status_code=303)

    rule = SubscriptionFilter(
        subscription_id=subscription_id,
        name=name, field_path=field_path,
        match_type=match_type, pattern=pattern, mode=mode,
    )
    db.add(rule)
    await db.commit()
    return RedirectResponse(f"/subscriptions/{subscription_id}/edit?msg=规则已添加&msg_type=success", status_code=303)


@router.post("/filters/{rule_id}/delete")
async def sub_filter_delete(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rule = (await db.execute(
        select(SubscriptionFilter)
        .where(SubscriptionFilter.id == rule_id)
        .options(selectinload(SubscriptionFilter.subscription))
    )).scalar_one_or_none()
    if rule and rule.subscription and rule.subscription.user_id == user.id:
        sub_id = rule.subscription_id
        await db.delete(rule)
        await db.commit()
        return RedirectResponse(f"/subscriptions/{sub_id}/edit?msg=规则已删除&msg_type=success", status_code=303)
    return RedirectResponse("/subscriptions", status_code=303)


@router.post("/filters/{rule_id}/toggle")
async def sub_filter_toggle(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rule = (await db.execute(
        select(SubscriptionFilter)
        .where(SubscriptionFilter.id == rule_id)
        .options(selectinload(SubscriptionFilter.subscription))
    )).scalar_one_or_none()
    if rule and rule.subscription and rule.subscription.user_id == user.id:
        rule.is_active = not rule.is_active
        await db.commit()
        return RedirectResponse(
            f"/subscriptions/{rule.subscription_id}/edit?msg=规则已{'启用' if rule.is_active else '禁用'}&msg_type=success",
            status_code=303
        )
    return RedirectResponse("/subscriptions", status_code=303)
