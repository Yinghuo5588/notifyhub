"""Webhook 处理主流程 —— v2 支持共享频道扇出"""
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import (
    Channel, WebhookLog, NotificationLog,
    ChannelSubscription,
)
from app.services.template_renderer import render_template_string
from app.services.filter_engine import apply_filters
from app.services.rate_limiter import (
    check_user_rate_limit, increment_counters, check_global_rate_limit,
)
from app.notifiers.registry import get_notifier


async def process_webhook(
    db: AsyncSession,
    channel: Channel,
    raw_body: str,
    parsed_data: dict,
    content_type: str,
    ip_address: str,
    headers_json: str,
) -> dict:
    """处理一个 webhook 请求的完整流程"""

    # 1. 记录原始请求
    wlog = WebhookLog(
        channel_id=channel.id,
        user_id=channel.user_id,
        request_headers=headers_json,
        request_body=raw_body[:50000],
        content_type=content_type,
        ip_address=ip_address,
        parsed_data=json.dumps(parsed_data, ensure_ascii=False, default=str)[:50000],
    )
    db.add(wlog)
    await db.flush()

    results = []

    # 2. 处理管理员自身通知（非共享场景 或 管理员也给自己配了模板+渠道）
    if channel.template and channel.notifier_config:
        r = await _process_owner(db, channel, wlog, parsed_data)
        results.append(r)

    # 3. 共享频道：扇出给所有活跃订阅者
    if channel.is_shared:
        sub_results = await _process_all_subscriptions(db, channel, wlog, parsed_data)
        results.extend(sub_results)

    # 4. 标记日志
    if not results:
        wlog.filter_passed = True
        wlog.filter_detail = "无处理目标"

    await db.commit()

    return {
        "status": "ok",
        "webhook_log_id": wlog.id,
        "targets_processed": len(results),
        "results": results,
    }


async def _process_owner(db, channel, wlog, parsed_data) -> dict:
    """处理频道拥有者的直接通知"""
    rules = [r for r in channel.filter_rules if r.is_active]
    passed, detail = apply_filters(parsed_data, rules)
    wlog.filter_passed = passed
    wlog.filter_detail = detail

    if not passed:
        return {"target": "owner", "status": "filtered", "detail": detail}

    return await _do_send(
        db=db,
        channel_id=channel.id,
        user_id=channel.user_id,
        wlog_id=wlog.id,
        template=channel.template,
        notifier_config=channel.notifier_config,
        parsed_data=parsed_data,
        recipients_override=None,
        tag="owner",
    )


async def _process_all_subscriptions(db, channel, wlog, parsed_data) -> list:
    """扇出到所有活跃订阅"""
    result = await db.execute(
        select(ChannelSubscription)
        .where(
            ChannelSubscription.channel_id == channel.id,
            ChannelSubscription.is_active == True,
        )
        .options(
            selectinload(ChannelSubscription.template),
            selectinload(ChannelSubscription.notifier_config),
            selectinload(ChannelSubscription.filters),
            selectinload(ChannelSubscription.user),
        )
    )
    subs = result.scalars().all()
    if not subs:
        return []

    results = []

    # 全局限频预检
    global_ok, global_msg = await check_global_rate_limit(db, channel)

    for sub in subs:
        try:
            r = await _process_one_subscription(db, channel, wlog, parsed_data, sub, global_ok, global_msg)
            results.append(r)
        except Exception as e:
            results.append({
                "target": f"user:{sub.user_id}",
                "status": "error",
                "detail": str(e)[:200],
            })

    return results


async def _process_one_subscription(db, channel, wlog, parsed_data, sub, global_ok, global_msg) -> dict:
    """处理单个订阅"""
    username = sub.user.username if sub.user else str(sub.user_id)
    tag = f"sub:{username}"

    # 检查用户账号是否活跃
    if sub.user and not sub.user.is_active:
        return {"target": tag, "status": "skipped", "detail": "用户已禁用"}

    # 检查模板
    if not sub.template:
        return {"target": tag, "status": "skipped", "detail": "未配置模板"}

    # 检查通知渠道
    if not sub.notifier_config:
        return {"target": tag, "status": "skipped", "detail": "未配置通知渠道"}

    # 订阅级过滤
    active_filters = [f for f in sub.filters if f.is_active]
    passed, detail = apply_filters(parsed_data, active_filters)
    if not passed:
        # 记录被过滤的日志
        nlog = NotificationLog(
            channel_id=channel.id,
            user_id=sub.user_id,
            webhook_log_id=wlog.id,
            notifier_type=sub.notifier_config.notifier_type,
            status="filtered",
            error_message=detail,
        )
        db.add(nlog)
        return {"target": tag, "status": "filtered", "detail": detail}

    # 全局限频
    if not global_ok:
        _record_rate_limited(db, channel, sub, wlog, global_msg)
        return {"target": tag, "status": "rate_limited", "detail": global_msg}

    # 用户限频
    user_ok, user_msg = check_user_rate_limit(sub, channel)
    if not user_ok:
        _record_rate_limited(db, channel, sub, wlog, user_msg)
        return {"target": tag, "status": "rate_limited", "detail": user_msg}

    # 确定收件人覆写
    recipients_override = None
    if sub.notifier_config.is_shared and sub.custom_recipients:
        recipients_override = sub.custom_recipients

    # 发送
    result = await _do_send(
        db=db,
        channel_id=channel.id,
        user_id=sub.user_id,
        wlog_id=wlog.id,
        template=sub.template,
        notifier_config=sub.notifier_config,
        parsed_data=parsed_data,
        recipients_override=recipients_override,
        tag=tag,
    )

    # 成功后递增计数器
    if result["status"] == "success":
        increment_counters(sub)

    return result


def _record_rate_limited(db, channel, sub, wlog, msg):
    """记录限频日志"""
    nlog = NotificationLog(
        channel_id=channel.id,
        user_id=sub.user_id,
        webhook_log_id=wlog.id,
        notifier_type=sub.notifier_config.notifier_type if sub.notifier_config else "",
        status="rate_limited",
        error_message=msg,
    )
    db.add(nlog)


async def _do_send(
    db, channel_id, user_id, wlog_id,
    template, notifier_config, parsed_data,
    recipients_override, tag,
) -> dict:
    """渲染模板 + 发送通知 + 记录日志"""
    subject = render_template_string(template.subject_template, parsed_data)
    body = render_template_string(template.body_template, parsed_data)

    nlog = NotificationLog(
        channel_id=channel_id,
        user_id=user_id,
        webhook_log_id=wlog_id,
        notifier_type=notifier_config.notifier_type,
        subject=subject,
        body=body,
        status="pending",
    )
    db.add(nlog)
    await db.flush()

    try:
        config = json.loads(notifier_config.config_json)

        # 覆写收件人
        if recipients_override:
            config["recipients"] = recipients_override

        notifier = get_notifier(notifier_config.notifier_type)
        if notifier is None:
            raise ValueError(f"不支持的通知类型: {notifier_config.notifier_type}")

        success = await notifier.send(
            subject=subject,
            body=body,
            body_format=template.body_format,
            config=config,
        )

        if success:
            nlog.status = "success"
        else:
            nlog.status = "failed"
            nlog.error_message = "发送返回失败"

    except Exception as e:
        nlog.status = "failed"
        nlog.error_message = str(e)[:1000]

    return {
        "target": tag,
        "status": nlog.status,
        "detail": nlog.error_message or "ok",
        "notification_log_id": nlog.id,
    }