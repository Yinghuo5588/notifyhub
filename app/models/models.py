"""所有数据库模型定义 —— v2 增加共享频道/共享通知/订阅"""
import uuid
import secrets
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utcnow():
    return datetime.now(timezone.utc)


def gen_uuid():
    return uuid.uuid4().hex


def gen_token():
    return secrets.token_urlsafe(32)


# ============================================================
# 用户
# ============================================================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(255), default="")
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    must_change_pwd = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)

    channels = relationship("Channel", back_populates="user", cascade="all,delete-orphan")
    templates = relationship("NotificationTemplate", back_populates="user", cascade="all,delete-orphan")
    notifier_configs = relationship("NotifierConfig", back_populates="user", cascade="all,delete-orphan")
    subscriptions = relationship("ChannelSubscription", back_populates="user", cascade="all,delete-orphan")
    shared_notifier_access = relationship("SharedNotifierAccess", back_populates="user", cascade="all,delete-orphan")
    shared_template_access = relationship("SharedTemplateAccess", back_populates="user", cascade="all,delete-orphan")


# ============================================================
# 通知模板
# ============================================================
class NotificationTemplate(Base):
    __tablename__ = "notification_templates"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    subject_template = Column(String(500), default="[通知] {{ title | default('新消息') }}")
    body_template = Column(Text, default="收到新通知:\n{{ data | tojson(indent=2) }}")
    body_format = Column(String(10), default="text")
    sample_data = Column(Text, default="{}")
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="templates")
    channels = relationship("Channel", back_populates="template")
    shared_access = relationship("SharedTemplateAccess", back_populates="template", cascade="all,delete-orphan")


# ============================================================
# 通知渠道配置（邮箱等）
# ============================================================
class NotifierConfig(Base):
    __tablename__ = "notifier_configs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    notifier_type = Column(String(50), default="email")
    config_json = Column(Text, default="{}")
    is_active = Column(Boolean, default=True)
    is_shared = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="notifier_configs")
    channels = relationship("Channel", back_populates="notifier_config")
    shared_access = relationship("SharedNotifierAccess", back_populates="notifier_config", cascade="all,delete-orphan")


# ============================================================
# Webhook 频道
# ============================================================
class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), default="")
    channel_uuid = Column(String(32), unique=True, default=gen_uuid, index=True)
    token = Column(String(64), default=gen_token)
    template_id = Column(Integer, ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True)
    notifier_config_id = Column(Integer, ForeignKey("notifier_configs.id", ondelete="SET NULL"), nullable=True)
    is_active = Column(Boolean, default=True)

    is_shared = Column(Boolean, default=False)
    per_hour_limit = Column(Integer, default=10)
    per_day_limit = Column(Integer, default=50)
    min_interval = Column(Integer, default=30)
    global_hour_limit = Column(Integer, default=100)
    global_day_limit = Column(Integer, default=500)

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    user = relationship("User", back_populates="channels")
    template = relationship("NotificationTemplate", back_populates="channels")
    notifier_config = relationship("NotifierConfig", back_populates="channels")
    filter_rules = relationship("FilterRule", back_populates="channel", cascade="all,delete-orphan")
    webhook_logs = relationship("WebhookLog", back_populates="channel", cascade="all,delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="channel", cascade="all,delete-orphan")
    subscriptions = relationship("ChannelSubscription", back_populates="channel", cascade="all,delete-orphan")


class FilterRule(Base):
    __tablename__ = "filter_rules"

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default="")
    field_path = Column(String(200), default="")
    match_type = Column(String(20), default="keyword")
    pattern = Column(String(500), nullable=False)
    mode = Column(String(10), default="blacklist")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    channel = relationship("Channel", back_populates="filter_rules")


class ChannelSubscription(Base):
    __tablename__ = "channel_subscriptions"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_user"),
    )

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    template_id = Column(Integer, ForeignKey("notification_templates.id", ondelete="SET NULL"), nullable=True)
    notifier_config_id = Column(Integer, ForeignKey("notifier_configs.id", ondelete="SET NULL"), nullable=True)
    custom_recipients = Column(String(500), default="")
    is_active = Column(Boolean, default=False)

    sends_today = Column(Integer, default=0)
    sends_this_hour = Column(Integer, default=0)
    last_send_at = Column(DateTime, nullable=True)
    hour_reset_at = Column(DateTime, nullable=True)
    day_reset_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    channel = relationship("Channel", back_populates="subscriptions")
    user = relationship("User", back_populates="subscriptions")
    template = relationship("NotificationTemplate", foreign_keys=[template_id])
    notifier_config = relationship("NotifierConfig", foreign_keys=[notifier_config_id])
    filters = relationship("SubscriptionFilter", back_populates="subscription", cascade="all,delete-orphan")


class SubscriptionFilter(Base):
    __tablename__ = "subscription_filters"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey("channel_subscriptions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), default="")
    field_path = Column(String(200), default="")
    match_type = Column(String(20), default="keyword")
    pattern = Column(String(500), nullable=False)
    mode = Column(String(10), default="blacklist")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    subscription = relationship("ChannelSubscription", back_populates="filters")


class SharedNotifierAccess(Base):
    __tablename__ = "shared_notifier_access"
    __table_args__ = (
        UniqueConstraint("notifier_config_id", "user_id", name="uq_notifier_user"),
    )

    id = Column(Integer, primary_key=True)
    notifier_config_id = Column(Integer, ForeignKey("notifier_configs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    notifier_config = relationship("NotifierConfig", back_populates="shared_access")
    user = relationship("User", back_populates="shared_notifier_access")


class SharedTemplateAccess(Base):
    __tablename__ = "shared_template_access"
    __table_args__ = (
        UniqueConstraint("template_id", "user_id", name="uq_template_user"),
    )

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("notification_templates.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    template = relationship("NotificationTemplate", back_populates="shared_access")
    user = relationship("User", back_populates="shared_template_access")


class WebhookLog(Base):
    __tablename__ = "webhook_logs"
    __table_args__ = (Index("idx_webhook_logs_created", "created_at"),)

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_headers = Column(Text, default="{}")
    request_body = Column(Text, default="")
    content_type = Column(String(200), default="")
    ip_address = Column(String(50), default="")
    parsed_data = Column(Text, default="{}")
    filter_passed = Column(Boolean, default=True)
    filter_detail = Column(String(500), default="")
    created_at = Column(DateTime, default=utcnow)

    channel = relationship("Channel", back_populates="webhook_logs")
    notification_log = relationship("NotificationLog", back_populates="webhook_log", uselist=False)


class NotificationLog(Base):
    __tablename__ = "notification_logs"
    __table_args__ = (Index("idx_notification_logs_created", "created_at"),)

    id = Column(Integer, primary_key=True)
    channel_id = Column(Integer, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    webhook_log_id = Column(Integer, ForeignKey("webhook_logs.id", ondelete="SET NULL"), nullable=True)
    notifier_type = Column(String(50), default="email")
    subject = Column(String(500), default="")
    body = Column(Text, default="")
    status = Column(String(20), default="pending")
    error_message = Column(Text, default="")
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=utcnow)

    channel = relationship("Channel", back_populates="notification_logs")
    webhook_log = relationship("WebhookLog", back_populates="notification_log")
