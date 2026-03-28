"""通知器注册表 —— 管理所有可用的通知渠道类型"""
from app.notifiers.base import BaseNotifier
from app.notifiers.email_notifier import EmailNotifier

# 所有已注册的通知器实例
_registry: dict[str, BaseNotifier] = {}


def _register(notifier_cls):
    """注册一个通知器类"""
    instance = notifier_cls()
    _registry[instance.notifier_type] = instance


# 注册所有通知器
_register(EmailNotifier)
# 未来扩展在这里添加:
# _register(BarkNotifier)
# _register(TelegramNotifier)


def get_notifier(notifier_type: str) -> BaseNotifier | None:
    """根据类型获取通知器实例"""
    return _registry.get(notifier_type)


def get_all_notifier_types() -> list[dict]:
    """获取所有可用的通知器类型信息"""
    return [
        {
            "type": n.notifier_type,
            "name": n.display_name,
            "schema": n.get_config_schema(),
        }
        for n in _registry.values()
    ]