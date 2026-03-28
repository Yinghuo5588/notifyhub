"""邮件通知器"""
import ssl
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.notifiers.base import BaseNotifier


class EmailNotifier(BaseNotifier):
    notifier_type = "email"
    display_name = "邮件通知"

    @classmethod
    def get_config_schema(cls) -> dict:
        return {
            "smtp_host": {"type": "text", "label": "SMTP服务器", "required": True, "placeholder": "smtp.qq.com"},
            "smtp_port": {"type": "number", "label": "端口", "required": True, "default": 465},
            "username": {"type": "text", "label": "用户名/邮箱", "required": True, "placeholder": "your@qq.com"},
            "password": {"type": "password", "label": "密码/授权码", "required": True, "placeholder": "SMTP授权码"},
            "use_ssl": {"type": "checkbox", "label": "使用SSL", "default": True},
            "use_tls": {"type": "checkbox", "label": "使用STARTTLS", "default": False},
            "from_name": {"type": "text", "label": "发件人名称", "required": False, "placeholder": "NotifyHub"},
            "recipients": {"type": "text", "label": "收件人（多个用逗号分隔）", "required": True, "placeholder": "a@example.com,b@example.com"},
        }

    async def send(self, subject: str, body: str, body_format: str, config: dict) -> bool:
        msg = MIMEMultipart("alternative")
        from_name = config.get("from_name", "NotifyHub")
        from_addr = config["username"]
        msg["From"] = f"{from_name} <{from_addr}>"
        msg["Subject"] = subject

        recipients = [r.strip() for r in config["recipients"].split(",") if r.strip()]
        msg["To"] = ", ".join(recipients)

        if body_format == "html":
            msg.attach(MIMEText(body, "html", "utf-8"))
        else:
            msg.attach(MIMEText(body, "plain", "utf-8"))

        port = int(config.get("smtp_port", 465))
        use_ssl = config.get("use_ssl", True)
        use_tls = config.get("use_tls", False)

        # 处理布尔值（可能从表单来的字符串）
        if isinstance(use_ssl, str):
            use_ssl = use_ssl.lower() in ("true", "1", "on", "yes")
        if isinstance(use_tls, str):
            use_tls = use_tls.lower() in ("true", "1", "on", "yes")

        smtp_kwargs = {
            "hostname": config["smtp_host"],
            "port": port,
            "username": config["username"],
            "password": config["password"],
            "timeout": 15,
        }

        if use_ssl:
            context = ssl.create_default_context()
            smtp_kwargs["use_tls"] = True  # aiosmtplib: use_tls = implicit SSL
            smtp_kwargs["tls_context"] = context
        elif use_tls:
            smtp_kwargs["start_tls"] = True  # STARTTLS

        await aiosmtplib.send(msg, **smtp_kwargs)
        return True

    async def test_connection(self, config: dict) -> tuple[bool, str]:
        try:
            await self.send(
                subject="NotifyHub 测试邮件",
                body="✅ 恭喜！邮件配置正确，此为测试邮件。\n\n—— NotifyHub",
                body_format="text",
                config=config,
            )
            return True, "测试邮件发送成功，请检查收件箱"
        except Exception as e:
            return False, f"发送失败: {str(e)}"