"""飞书群机器人通知器 —— 支持 Webhook + 加签密钥"""
import asyncio
import hashlib
import hmac
import time
import json
import httpx
from app.notifiers.base import BaseNotifier


class FeishuNotifier(BaseNotifier):
    notifier_type = "feishu"
    display_name = "飞书群机器人"

    @classmethod
    def get_config_schema(cls) -> dict:
        return {
            "webhook_url": {
                "type": "text",
                "label": "Webhook 地址",
                "required": True,
                "placeholder": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx",
            },
            "secret": {
                "type": "text",
                "label": "加签密钥（可选）",
                "required": False,
                "placeholder": "群机器人设置中的加签密钥",
            },
            "bot_name": {
                "type": "text",
                "label": "机器人名字（可选）",
                "required": False,
                "placeholder": "NotifyHub",
            },
        }

    async def send(
        self,
        subject: str,
        body: str,
        body_format: str,
        config: dict,
    ) -> bool:
        webhook_url = config["webhook_url"].strip()
        secret = config.get("secret", "").strip()
        bot_name = config.get("bot_name", "NotifyHub").strip()

        # 构建飞书卡片消息
        content = {
            "msg_type": "interactive",
            "card": {
                "config": {"wide_screen_mode": True},
                "header": {
                    "title": {"tag": "plain_text", "content": subject or "NotifyHub 通知"},
                    "template": "purple" if "警告" in (subject or "") else "blue",
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": body or "(无正文)",
                        },
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {"tag": "plain_text", "content": f"🤖 {bot_name} · {time.strftime('%Y-%m-%d %H:%M:%S')}"},
                        ],
                    },
                ],
            },
        }

        payload = json.dumps(content).encode("utf-8")

        # 加签逻辑
        if secret:
            timestamp = str(int(time.time()))
            string_to_sign = f"{timestamp}\n{secret}"
            sign = hmac.new(
                string_to_sign.encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()
            separator = "&" if "?" in webhook_url else "?"
            webhook_url = f"{webhook_url}{separator}timestamp={timestamp}&sign={sign}"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                webhook_url,
                content=payload,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("code") != 0 and result.get("StatusCode") != 0:
                raise RuntimeError(f"飞书返回错误: {result}")
            return True

    async def test_connection(self, config: dict) -> tuple[bool, str]:
        try:
            await self.send(
                subject="✅ 飞书通知测试",
                body="🎉 **恭喜！**\n\n飞书群机器人配置正确，此为测试消息。\n\n—— NotifyHub",
                body_format="text",
                config=config,
            )
            return True, "测试消息发送成功，请检查群聊"
        except Exception as e:
            return False, f"发送失败: {str(e)}"
