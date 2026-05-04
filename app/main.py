"""NotifyHub 应用入口 - Vue SPA 生产入口版"""
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse, JSONResponse, FileResponse
from sqlalchemy import select

from app.config import (
    STATIC_DIR,
    FRONTEND_DIR,
    DEBUG,
    ADMIN_USERNAME,
    ADMIN_PASSWORD,
)
from app.core.database import init_db, async_session_factory
from app.core.security import hash_password
from app.models.models import User, NotificationTemplate


async def seed_admin():
    """首次启动: 创建管理员账号和示例模板"""
    async with async_session_factory() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        admin = User(
            username=ADMIN_USERNAME,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_admin=True,
            must_change_pwd=True,
        )
        db.add(admin)
        await db.flush()

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
                sample_data=json.dumps(
                    {
                        "title": "测试标题",
                        "message": "这是一条测试消息",
                    },
                    ensure_ascii=False,
                ),
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
                sample_data=json.dumps(
                    {
                        "Event": "library.new",
                        "Item": {
                            "Name": "第1集",
                            "SeriesName": "示例剧集",
                            "Type": "Episode",
                            "ParentIndexNumber": 1,
                            "IndexNumber": 1,
                            "Overview": "这是剧情简介",
                        },
                    },
                    ensure_ascii=False,
                ),
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
                sample_data=json.dumps(
                    {
                        "name": "签到任务",
                        "status": "完成",
                        "message": "签到成功,获得10积分",
                    },
                    ensure_ascii=False,
                ),
            ),
        ]

        for item in samples:
            db.add(item)

        await db.commit()
        print(f"✅ 管理员账号已创建: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
        print("⚠️  请登录后立即修改默认密码!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()
    await seed_admin()
    print("🚀 NotifyHub 启动成功")
    yield
    print("👋 NotifyHub 已停止")


app = FastAPI(
    title="NotifyHub",
    lifespan=lifespan,
    docs_url="/api/docs" if DEBUG else None,
    redoc_url="/api/redoc" if DEBUG else None,
    openapi_url="/api/openapi.json" if DEBUG else None,
)


# ------------------------------------------------------------
# 静态资源
# ------------------------------------------------------------

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

assets_dir = FRONTEND_DIR / "assets"
if assets_dir.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(assets_dir)),
        name="frontend-assets",
    )


# ------------------------------------------------------------
# 注册 API 路由
# ------------------------------------------------------------

from app.routes.api import (
    auth as api_auth,
    dashboard as api_dashboard,
    channels as api_channels,
    templates as api_templates,
    notifiers as api_notifiers,
    settings as api_settings,
    history as api_history,
    logs as api_logs,
    subscriptions as api_subscriptions,
    admin as api_admin,
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


# ------------------------------------------------------------
# Webhook 路由必须保留
# ------------------------------------------------------------

from app.routes import webhook

app.include_router(webhook.router)


# ------------------------------------------------------------
# 异常处理
# ------------------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    API 返回 JSON。
    SPA 页面请求交给 Vue 自己处理。
    """
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    if request.url.path.startswith("/hook/"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    # 非 API 的异常，生产入口下回到 SPA
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局兜底异常处理。
    API 返回 JSON。
    非 API 在生产入口下返回 SPA。
    """
    if DEBUG:
        raise exc

    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    if request.url.path.startswith("/hook/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"},
    )


# ------------------------------------------------------------
# Vue SPA 入口
# ------------------------------------------------------------

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    Vue SPA catch-all。

    注意：
    - /api/* 不返回 index.html
    - /hook/* 不返回 index.html
    - /static/* 不返回 index.html
    - /assets/* 由 StaticFiles 处理
    """
    if full_path.startswith("api"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    if full_path.startswith("hook"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    if full_path.startswith("static"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    if full_path.startswith("assets"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)

    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        return JSONResponse(
            {
                "detail": (
                    "Frontend not built. Please run: "
                    "cd frontend && npm install && npm run build"
                )
            },
            status_code=500,
        )

    return FileResponse(str(index_file))