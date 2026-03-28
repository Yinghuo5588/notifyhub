"""通知渠道抽象基类 —— 所有通知器都继承此类"""
from abc import ABC, abstractmethod


class BaseNotifier(ABC):
    """通知器基类"""

    notifier_type: str = ""
    display_name: str = ""

    @abstractmethod
    async def send(
        self,
        subject: str,
        body: str,
        body_format: str,
        config: dict,
    ) -> bool:
        """
        发送通知
        :param subject: 标题
        :param body: 正文
        :param body_format: 格式 text/html
        :param config: 渠道配置字典
        :return: 是否成功
        """
        pass

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> dict:
        """
        返回配置表单字段定义
        前端根据此结构自动生成表单
        """
        pass

    @abstractmethod
    async def test_connection(self, config: dict) -> tuple[bool, str]:
        """测试连接，返回 (成功与否, 描述信息)"""
        pass