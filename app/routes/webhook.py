"""Webhook 接收端点 —— 外部应用调用此接口"""
import json
from fastapi import APIRouter, Request, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory
from app.models.models import Channel
from app.services.webhook_processor import process_webhook

router = APIRouter()


@router.api_route("/hook/{channel_uuid}", methods=["GET", "POST", "PUT"])
async def receive_webhook(
    channel_uuid: str,
    request: Request,
    token: str = Query(None),
    authorization: str = Header(None),
    x_token: str = Header(None),
):
    """
    Webhook 接收端点
    Token 支持三种传递方式:
      1. Query参数: ?token=xxx
      2. Header: Authorization: Bearer xxx
      3. Header: X-Token: xxx
    """
    # 确定Token
    req_token = token
    if not req_token and authorization:
        if authorization.startswith("Bearer "):
            req_token = authorization[7:]
        else:
            req_token = authorization
    if not req_token and x_token:
        req_token = x_token

    # 查找频道
    async with async_session_factory() as db:
        result = await db.execute(
            select(Channel)
            .where(Channel.channel_uuid == channel_uuid)
            .options(
                selectinload(Channel.template),
                selectinload(Channel.notifier_config),
                selectinload(Channel.filter_rules),
            )
        )
        channel = result.scalar_one_or_none()

        if not channel:
            return JSONResponse({"error": "频道不存在"}, status_code=404)

        if not channel.is_active:
            return JSONResponse({"error": "频道已禁用"}, status_code=403)

        # 验证Token
        if channel.token and channel.token != req_token:
            return JSONResponse({"error": "Token验证失败"}, status_code=401)

        # 解析请求体
        content_type = request.headers.get("content-type", "")
        raw_body = ""
        parsed_data = {}

        try:
            if request.method == "GET":
                parsed_data = dict(request.query_params)
                raw_body = str(parsed_data)
            elif "application/json" in content_type:
                raw_body = (await request.body()).decode("utf-8", errors="replace")
                parsed_data = json.loads(raw_body) if raw_body else {}
            elif "multipart/form-data" in content_type:
                form = await request.form()
                raw_parts = {}
                for key in form:
                    value = form[key]
                    if hasattr(value, "read"):
                        content = (await value.read()).decode("utf-8", errors="replace")
                        try:
                            raw_parts[key] = json.loads(content)
                        except Exception:
                            raw_parts[key] = content
                    else:
                        try:
                            raw_parts[key] = json.loads(value)
                        except Exception:
                            raw_parts[key] = value
                parsed_data = raw_parts
                raw_body = json.dumps(raw_parts, ensure_ascii=False, default=str)
                # 如果只有一个字段且是dict，展平它
                if len(parsed_data) == 1:
                    only_val = list(parsed_data.values())[0]
                    if isinstance(only_val, dict):
                        parsed_data = only_val
            elif "application/x-www-form-urlencoded" in content_type:
                form = await request.form()
                parsed_data = dict(form)
                raw_body = str(parsed_data)
            else:
                raw_body = (await request.body()).decode("utf-8", errors="replace")
                try:
                    parsed_data = json.loads(raw_body)
                except Exception:
                    parsed_data = {"_raw": raw_body}
        except Exception as e:
            parsed_data = {"_parse_error": str(e)}
            raw_body = str(e)

        # 安全获取请求头
        headers_dict = dict(request.headers)
        headers_json = json.dumps(headers_dict, ensure_ascii=False)

        # IP
        ip = request.client.host if request.client else "unknown"

        # 处理
        result = await process_webhook(
            db=db,
            channel=channel,
            raw_body=raw_body,
            parsed_data=parsed_data,
            content_type=content_type,
            ip_address=ip,
            headers_json=headers_json,
        )
        return JSONResponse(result)