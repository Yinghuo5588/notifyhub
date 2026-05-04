"""NotifyHub 应用入口"""
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select

from app.config import STATIC_DIR, DEBUG, ADMIN_USERNAME, ADMIN_PASSWORD
from app.core.database import init_db, async_session_factory
from app.core.security import hash_password
from app.models.models import User, NotificationTemplate


async def seed_admin():
    """首次启动：创建管理员账号和示例模板"""
    async with async_session_factory() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return  # 已有用户，跳过

        admin = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_admin=True,
            must_change_pwd=True,
        )
        db.add(admin)
        await db.flush()

        # 创建示例模板
        samples = [
            NotificationTemplate(
                user_id=admin.id,
                name="通用通知模板",
                description="适用于任何Webhook的通用模板",
                subject_template="[通知] {{ title | default('新消息') }}",
                body_template=(
                    "📬 收到新通知\n\n"
                    "{% if title is defined %}标题: {{ title }}{% endif %}\n"
                    "{% if message is defined %}内容: {{ message }}{% endif %}\n\n"
                    "{% if data is defined %}原始数据:\n{{ data | tojson(indent=2) }}{% endif %}\n\n"
                    "时间: {{ _timestamp }}"
                ),
                body_format="text",
                sample_data=json.dumps({"title": "测试标题", "message": "这是一条测试消息"}, ensure_ascii=False),
            ),
            NotificationTemplate(
                user_id=admin.id,
                name="Emby 入库通知",
                description="Emby/Jellyfin 媒体入库通知模板",
                subject_template="[Emby] {{ Item.SeriesName | default(Item.Name) | default('媒体更新') }}",
                body_template=(
                    "🎬 Emby 媒体更新\n\n"
                    "事件: {{ Event | default('未知') }}\n"
                    "{% if Item.SeriesName is defined %}"
                    "剧集: {{ Item.SeriesName }}\n"
                    "集数: S{{ Item.ParentIndexNumber | default('?') }}E{{ Item.IndexNumber | default('?') }}\n"
                    "标题: {{ Item.Name }}\n"
                    "{% else %}"
                    "名称: {{ Item.Name | default('未知') }}\n"
                    "类型: {{ Item.Type | default('未知') }}\n"
                    "{% endif %}"
                    "{% if Item.Overview is defined %}\n简介: {{ Item.Overview }}{% endif %}\n\n"
                    "时间: {{ _timestamp }}"
                ),
                body_format="text",
                sample_data=json.dumps({
                    "Event": "library.new",
                    "Item": {
                        "Name": "第1集", "SeriesName": "示例剧集",
                        "Type": "Episode", "ParentIndexNumber": 1,
                        "IndexNumber": 1, "Overview": "这是剧情简介"
                    }
                }, ensure_ascii=False),
            ),
            NotificationTemplate(
                user_id=admin.id,
                name="青龙面板通知",
                description="青龙面板任务执行结果通知",
                subject_template="[青龙] {{ name | default('任务通知') }}",
                body_template=(
                    "📋 青龙面板通知\n\n"
                    "任务: {{ name | default('未知') }}\n"
                    "状态: {{ status | default('未知') }}\n"
                    "{% if message is defined %}详情: {{ message }}{% endif %}\n\n"
                    "时间: {{ _timestamp }}"
                ),
                body_format="text",
                sample_data=json.dumps({
                    "name": "签到任务", "status": "完成", "message": "签到成功，获得10积分"
                }, ensure_ascii=False),
            ),
        ]
        for s in samples:
            db.add(s)
        await db.commit()
        print(f"✅ 管理员账号已创建: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print("⚠️  请登录后立即修改默认密码！")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await seed_admin()
    print("🚀 NotifyHub 启动成功")
    yield
    print("👋 NotifyHub 已停止")


app = FastAPI(title="NotifyHub", lifespan=lifespan, docs_url="/api/docs" if DEBUG else None)

# 静态文件
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# 注册旧页面路由
from app.routes import (
    auth, dashboard, channels, templates, notifiers, filters,
    history, logs, settings, admin, webhook, subscriptions,
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(channels.router)
app.include_router(templates.router)
app.include_router(notifiers.router)
app.include_router(filters.router)
app.include_router(history.router)
app.include_router(logs.router)
app.include_router(settings.router)
app.include_router(admin.router)
app.include_router(subscriptions.router)
app.include_router(webhook.router)

# 注册 JSON API 路由
from app.routes.api import (
    auth as api_auth,
    dashboard as api_dashboard,
    channels as api_channels,
    templates as api_templates,
    notifiers as api_notifiers,
    settings as api_settings,
    history as api_history,
    logs as api_logs,
)

app.include_router(api_auth.router, prefix="/api")
app.include_router(api_dashboard.router, prefix="/api")
app.include_router(api_channels.router, prefix="/api")
app.include_router(api_templates.router, prefix="/api")
app.include_router(api_notifiers.router, prefix="/api")
app.include_router(api_settings.router, prefix="/api")
app.include_router(api_history.router, prefix="/api")
app.include_router(api_logs.router, prefix="/api")
app.include_router(api_subscriptions.router, prefix="/api")
app.include_router(api_admin.router, prefix="/api")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    区分 API 和旧页面错误处理。

    /api/*:
    - 返回 JSON

    旧页面:
    - 保持原来的重定向体验
    """
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    if exc.status_code == 302:
        return RedirectResponse(
            exc.headers.get("Location", "/login"),
            status_code=303,
        )

    if exc.status_code == 401:
        return RedirectResponse("/login", status_code=303)

    if exc.status_code == 403:
        return RedirectResponse(
            "/?msg=无权限&msg_type=error",
            status_code=303,
        )

    return RedirectResponse(
        "/?msg=发生错误&msg_type=error",
        status_code=303,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局兜底异常处理。

    注意:
    - API 返回 JSON
    - 页面继续重定向
    """
    if request.url.path.startswith("/api/"):
        if DEBUG:
            raise exc
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    if hasattr(exc, "status_code") and exc.status_code == 302:
        return RedirectResponse(
            exc.headers.get("Location", "/login"),
            status_code=303,
        )

    if DEBUG:
        raise exc

    return RedirectResponse(
        "/?msg=发生错误&msg_type=error",
        status_code=303,
    )