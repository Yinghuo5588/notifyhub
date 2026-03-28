"""数据库连接管理"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def _get_table_columns(conn, table_name: str) -> set[str]:
    result = await conn.execute(text(f"PRAGMA table_info({table_name})"))
    return {row[1] for row in result.fetchall()}


async def _ensure_sqlite_schema(conn):
    """为旧版 SQLite 数据库补齐新增字段/表，避免升级后页面直接报错。"""
    from app.models.models import Base

    await conn.run_sync(Base.metadata.create_all)

    channel_cols = await _get_table_columns(conn, "channels")
    if "is_shared" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN is_shared BOOLEAN DEFAULT 0"))
    if "per_hour_limit" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN per_hour_limit INTEGER DEFAULT 10"))
    if "per_day_limit" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN per_day_limit INTEGER DEFAULT 50"))
    if "min_interval" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN min_interval INTEGER DEFAULT 30"))
    if "global_hour_limit" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN global_hour_limit INTEGER DEFAULT 100"))
    if "global_day_limit" not in channel_cols:
        await conn.execute(text("ALTER TABLE channels ADD COLUMN global_day_limit INTEGER DEFAULT 500"))

    template_cols = await _get_table_columns(conn, "notification_templates")
    if "is_shared" not in template_cols:
        await conn.execute(text("ALTER TABLE notification_templates ADD COLUMN is_shared BOOLEAN DEFAULT 0"))

    notifier_cols = await _get_table_columns(conn, "notifier_configs")
    if "is_shared" not in notifier_cols:
        await conn.execute(text("ALTER TABLE notifier_configs ADD COLUMN is_shared BOOLEAN DEFAULT 0"))

    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS shared_template_access (
            id INTEGER PRIMARY KEY,
            template_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME,
            CONSTRAINT uq_template_user UNIQUE (template_id, user_id),
            FOREIGN KEY(template_id) REFERENCES notification_templates (id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS shared_notifier_access (
            id INTEGER PRIMARY KEY,
            notifier_config_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at DATETIME,
            CONSTRAINT uq_notifier_user UNIQUE (notifier_config_id, user_id),
            FOREIGN KEY(notifier_config_id) REFERENCES notifier_configs (id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS channel_subscriptions (
            id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            template_id INTEGER,
            notifier_config_id INTEGER,
            custom_recipients VARCHAR(500) DEFAULT '',
            is_active BOOLEAN DEFAULT 0,
            sends_today INTEGER DEFAULT 0,
            sends_this_hour INTEGER DEFAULT 0,
            last_send_at DATETIME,
            hour_reset_at DATETIME,
            day_reset_at DATETIME,
            created_at DATETIME,
            CONSTRAINT uq_channel_user UNIQUE (channel_id, user_id),
            FOREIGN KEY(channel_id) REFERENCES channels (id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY(template_id) REFERENCES notification_templates (id) ON DELETE SET NULL,
            FOREIGN KEY(notifier_config_id) REFERENCES notifier_configs (id) ON DELETE SET NULL
        )
    """))
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS subscription_filters (
            id INTEGER PRIMARY KEY,
            subscription_id INTEGER NOT NULL,
            name VARCHAR(100) DEFAULT '',
            field_path VARCHAR(200) DEFAULT '',
            match_type VARCHAR(20) DEFAULT 'keyword',
            pattern VARCHAR(500) NOT NULL,
            mode VARCHAR(10) DEFAULT 'blacklist',
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME,
            FOREIGN KEY(subscription_id) REFERENCES channel_subscriptions (id) ON DELETE CASCADE
        )
    """))


async def init_db():
    """初始化数据库表并为旧版数据库补齐新增结构"""
    async with engine.begin() as conn:
        await _ensure_sqlite_schema(conn)
