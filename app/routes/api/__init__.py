"""NotifyHub JSON API routes."""
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

__all__ = [
    "api_auth",
    "api_dashboard",
    "api_channels",
    "api_templates",
    "api_notifiers",
    "api_settings",
    "api_history",
    "api_logs",
    "api_subscriptions",
    "api_admin",
]