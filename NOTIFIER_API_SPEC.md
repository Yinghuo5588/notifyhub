# NOTIFIER_API_SPEC.md

> NotifyHub 通知渠道接口规范文档。
>
> 本文档定义 `BaseNotifier` 的职责、方法签名、返回约定、配置 schema 规范，以及未来新增通知渠道时应遵守的统一实现规则。

---

## 1. 设计目标

NotifyHub 的通知渠道（Notifier）采用插件式设计。

目标是：
- 新增渠道时尽量不改主业务流程
- 新增渠道时尽量不改数据库结构
- 通过统一接口，让模板渲染、发送测试、发送历史记录、共享逻辑都能复用

当前渠道扩展机制由以下文件组成：

- `app/notifiers/base.py`：抽象基类
- `app/notifiers/registry.py`：渠道注册中心
- `app/notifiers/email_notifier.py`：现有示例实现

---

## 2. 当前基类接口（真实现状）

当前 `BaseNotifier` 定义如下：

```python
class BaseNotifier(ABC):
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
        ...

    @classmethod
    @abstractmethod
    def get_config_schema(cls) -> dict:
        ...

    @abstractmethod
    async def test_connection(self, config: dict) -> tuple[bool, str]:
        ...
```

这就是当前项目实际使用的规范。后续扩展渠道时，默认必须兼容它。

---

## 3. BaseNotifier 约束说明

### 3.1 `notifier_type`
唯一字符串标识，用于：
- 存储到数据库字段 `NotifierConfig.notifier_type`
- 从 registry 中查找对应 notifier
- 在前端渠道列表中显示类型

#### 要求
- 必须唯一
- 使用小写英文 + 下划线命名
- 一旦投入使用，不要轻易修改

#### 推荐示例
- `email`
- `wecom_bot`
- `feishu_bot`
- `telegram_bot`
- `bark`
- `dingtalk_bot`

---

### 3.2 `display_name`
用于前端展示的人类可读名称。

#### 示例
- `邮件通知`
- `企业微信机器人`
- `飞书机器人`
- `Telegram Bot`

#### 要求
- 简洁
- 面向用户
- 不要写成程序内部代号

---

## 4. `send()` 规范

### 当前签名
```python
async def send(
    self,
    subject: str,
    body: str,
    body_format: str,
    config: dict,
) -> bool:
```

### 参数说明

#### `subject: str`
通知标题。

说明：
- 并非所有渠道都天然支持标题
- 对于不支持标题的渠道，可以自行拼接到正文中
- 不应要求调用方为不同 provider 特判标题逻辑

#### `body: str`
通知正文。

说明：
- 这是模板渲染后的最终内容
- 通常已经是纯文本或 HTML

#### `body_format: str`
正文格式。

当前常见值：
- `text`
- `html`

说明：
- 某些渠道不支持 HTML 时，应在 notifier 内自行降级
- 例如：移除 HTML 标签、转成纯文本、忽略标题等

#### `config: dict`
渠道配置字典，来源于数据库中的 `config_json`。

说明：
- 由当前 notifier 的 `get_config_schema()` 决定结构
- notifier 内部应自行校验必填项

---

### 返回值规范
返回：
```python
bool
```

#### 语义
- `True`：发送成功
- 抛异常：发送失败

#### 为什么不推荐返回 `False`
当前主流程更适合：
- 成功返回 `True`
- 失败抛出异常，由上层统一记录失败日志

因此建议：
- 成功：`return True`
- 失败：抛出明确异常

不要静默失败。

---

### `send()` 内部建议责任
每个 notifier 的 `send()` 应负责：
- 读取并校验配置
- 将标准消息转换为 provider 请求格式
- 发起 HTTP / SMTP / SDK 调用
- 处理超时
- 将 provider 错误转换为可理解异常

### `send()` 不应负责
- 渲染模板
- 判断是否限流
- 判断是否过滤
- 写数据库日志
- 路由层请求解析

这些已由上层负责。

---

## 5. `get_config_schema()` 规范

### 当前签名
```python
@classmethod
def get_config_schema(cls) -> dict:
```

### 作用
返回用于前端动态生成配置表单的 schema。

前端当前会根据它渲染新建 / 编辑通知渠道页面。

---

### 当前推荐字段结构
示例：

```python
{
    "smtp_host": {
        "type": "text",
        "label": "SMTP服务器",
        "required": True,
        "placeholder": "smtp.qq.com"
    },
    "smtp_port": {
        "type": "number",
        "label": "端口",
        "required": True,
        "default": 465
    },
    "use_ssl": {
        "type": "checkbox",
        "label": "使用SSL",
        "default": True
    }
}
```

---

### 支持字段说明

#### `type`
当前前端已知兼容：
- `text`
- `password`
- `number`
- `checkbox`

如果新增其他类型（如 `textarea`, `select`, `url`），需要同步扩展前端渲染逻辑。

#### `label`
字段展示名称。

#### `required`
是否必填。

#### `default`
默认值。

#### `placeholder`
输入框提示。

---

### schema 设计原则

#### 1. 字段命名要稳定
避免已发布后频繁改 key，否则旧 `config_json` 兼容会变麻烦。

#### 2. 尽量保持简洁
不要把一个 notifier 做成几十个字段的大杂烩。

#### 3. 同类 provider 拆成不同 notifier
例如：
- 企业微信机器人 `wecom_bot`
- 企业微信应用消息 `wecom_app`

不要把两套完全不同的鉴权方式硬塞一个 schema。

---

## 6. `test_connection()` 规范

### 当前签名
```python
async def test_connection(self, config: dict) -> tuple[bool, str]:
```

### 返回值
```python
(ok: bool, msg: str)
```

#### 语义
- `ok = True`：测试成功
- `ok = False`：测试失败
- `msg`：用于直接展示给用户的消息

---

### 建议行为
- 发一条最小测试消息
- 不依赖业务模板
- 不写发送历史
- 返回简洁明确的提示

#### 成功示例
- `测试消息发送成功`
- `测试邮件发送成功，请检查收件箱`

#### 失败示例
- `Webhook 地址无效`
- `认证失败`
- `签名错误`
- `chat_id 不存在`
- `请求超时`

---

## 7. registry 规范

### 当前 registry 职责
文件：
```python
app/notifiers/registry.py
```

负责：
- 注册 notifier
- 获取 notifier 实例
- 向前端暴露所有可用类型 + schema

### 当前注册方式
```python
_register(EmailNotifier)
# _register(BarkNotifier)
# _register(TelegramNotifier)
```

### 新增渠道时必须做
在 `registry.py` 中注册，否则：
- 前端不会显示该渠道
- `get_notifier()` 无法找到该类型
- 主流程发送会失败

---

## 8. 新增渠道标准模板

建议以后新增渠道时，统一用这个骨架：

```python
from app.notifiers.base import BaseNotifier

class ExampleNotifier(BaseNotifier):
    notifier_type = "example"
    display_name = "示例通知"

    @classmethod
    def get_config_schema(cls) -> dict:
        return {
            "api_key": {
                "type": "password",
                "label": "API Key",
                "required": True,
                "placeholder": "请输入 API Key"
            },
            "target": {
                "type": "text",
                "label": "目标地址",
                "required": True,
                "placeholder": "如群ID / chat_id / webhook"
            }
        }

    async def send(self, subject: str, body: str, body_format: str, config: dict) -> bool:
        # 1. 校验配置
        # 2. 转换消息格式
        # 3. 调用 provider
        # 4. 成功返回 True，失败抛异常
        return True

    async def test_connection(self, config: dict) -> tuple[bool, str]:
        try:
            await self.send(
                subject="NotifyHub 测试通知",
                body="测试消息",
                body_format="text",
                config=config,
            )
            return True, "测试发送成功"
        except Exception as e:
            return False, f"测试发送失败: {str(e)}"
```

---

## 9. 对消息格式的处理建议

不同 provider 能力不同，因此 notifier 内应负责做消息格式适配。

### 统一输入
上层只会给你：
- `subject`
- `body`
- `body_format`

### notifier 内部需要考虑

#### 如果 provider 不支持标题
可以：
- 将标题拼到正文前面
- 或直接忽略标题

#### 如果 provider 不支持 HTML
可以：
- 转纯文本
- 去标签
- 保留主要内容

#### 如果 provider 有长度限制
可以：
- 截断正文
- 增加省略号
- 抛出明确错误

#### 如果 provider 支持 markdown / card
可以在 notifier 内做适配，但不要要求上层写 provider 专属模板逻辑。

---

## 10. 错误处理规范

### 原则
对用户友好，对开发者可调试。

#### 对用户
返回可理解错误：
- `飞书发送失败：Webhook 地址无效`
- `企业微信发送失败：签名校验失败`

#### 对日志
建议保留：
- provider 状态码
- 原始响应 body
- 请求目标 URL（必要时脱敏）
- 超时信息

### 不推荐
- 直接抛难懂 SDK 错误给前端
- 把 provider 完整 HTML 报错页原样显示给用户

---

## 11. 共享渠道场景的注意事项

当前系统支持共享通知渠道给其他用户使用。

因此新增 notifier 时，需要先明确：

### 这个渠道是否适合共享？
例如：
- 邮件：可以共享，但可允许用户自定义收件人
- 企业微信机器人：通常不适合让订阅用户改 webhook
- 飞书机器人：通常也不适合让用户改 webhook

### 建议
默认保持保守：
- 核心配置只能由拥有者维护
- 如有覆盖能力，仅开放极少数字段

不要默认让订阅用户可修改关键凭据。

---

## 12. 未来推荐扩展的接口能力（可选）

当前接口已够用，但如果渠道变多，未来可考虑扩展以下能力。

### 可选增强字段
- `supports_html`
- `supports_markdown`
- `supports_title`
- `supports_attachments`
- `supports_mentions`
- `supports_shared_override_fields`

### 目的
让系统未来能更智能地：
- 渲染不同格式
- 降级发送能力
- 控制共享可覆盖字段

当前不是必须，但后续规模变大时会有帮助。

---

## 13. 新增渠道实现 checklist

### 必做
- [ ] 新建 notifier 文件
- [ ] 继承 `BaseNotifier`
- [ ] 定义 `notifier_type`
- [ ] 定义 `display_name`
- [ ] 实现 `get_config_schema()`
- [ ] 实现 `send()`
- [ ] 实现 `test_connection()`
- [ ] 在 `registry.py` 注册

### 联调
- [ ] 前端创建页可看到该渠道
- [ ] 表单字段能正确渲染
- [ ] 保存配置成功
- [ ] 测试发送成功 / 失败提示正确
- [ ] 实际通知发送正常
- [ ] 发送历史可追踪

---

## 14. 当前规范结论

NotifyHub 的 Notifier 接口虽然简单，但已经足够支撑：
- 邮件
- 企业微信机器人
- 飞书机器人
- Telegram Bot
- Bark
- 钉钉机器人

这套规范的核心思想是：

> 上层流程统一，provider 差异在 notifier 内部被吸收。

只要继续遵守本规范，后续扩展新渠道不会失控。
