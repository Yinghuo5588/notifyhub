# NotifyHub 开发文档

> 面向后续维护与扩展，尤其是新增通知渠道（如企业微信、飞书、Telegram、Bark、钉钉等）。

---

## 1. 项目定位

NotifyHub 是一个 **Webhook 通知中继 / 分发平台**。

核心流程：

1. 外部系统通过 Webhook 将事件打进来
2. 系统解析原始数据
3. 过滤器决定是否发送
4. 模板渲染生成标题 / 正文
5. 限流器判断是否允许发送
6. 调用具体通知渠道发送
7. 记录发送历史与请求日志

它本质上是一个：

- Webhook 接收器
- 规则过滤器
- 模板渲染器
- 多通知渠道分发器
- 可视化管理后台

---

## 2. 当前项目结构

```text
app/
  main.py                 应用入口
  config.py               全局配置
  core/
    database.py           数据库初始化 / Session
    dependencies.py       登录用户等依赖注入
    security.py           密码 / JWT 等安全逻辑
  models/
    models.py             SQLAlchemy 数据模型
  routes/
    auth.py               登录 / 注销
    dashboard.py          仪表盘
    channels.py           Webhook 频道管理
    templates.py          通知模板管理
    notifiers.py          通知渠道管理
    filters.py            过滤规则管理
    history.py            发送历史
    logs.py               Webhook 请求日志
    settings.py           用户设置
    admin.py              管理员功能 / 共享功能
    subscriptions.py      用户订阅共享频道
    webhook.py            Webhook 接收入口
  services/
    webhook_processor.py  Webhook 主处理流程
    template_renderer.py  模板渲染
    filter_engine.py      过滤规则判断
    rate_limiter.py       限流逻辑
  notifiers/
    base.py               通知渠道抽象基类
    registry.py           渠道注册中心
    email_notifier.py     当前已实现的邮箱渠道
templates/
static/
```

---

## 3. 核心业务对象

### 3.1 Channel（频道）
Webhook 接收入口。

每个频道通常包含：
- 名称
- 描述
- 对应模板
- 对应通知渠道配置
- 是否启用
- 过滤规则
- 限流参数
- 共享设置（管理员）

### 3.2 NotificationTemplate（通知模板）
负责把原始结构化数据渲染成最终通知文本。

支持：
- subject_template
- body_template
- body_format
- sample_data

### 3.3 NotifierConfig（通知渠道配置）
某个具体通知渠道实例的配置。

例如：
- 邮箱 SMTP 配置
- 企业微信机器人 webhook 地址
- 飞书 bot webhook 地址
- Telegram bot token + chat id

当前数据存储方式：
- `notifier_type`: 标识渠道类型（如 `email`）
- `config_json`: 存储该渠道的配置 JSON

### 3.4 NotificationLog（发送日志）
记录通知发送结果。

用于：
- 成功 / 失败追踪
- 重发
- 发送历史查看

### 3.5 WebhookLog（请求日志）
记录原始 Webhook 请求。

用于：
- 调试入站请求
- 查看原始 JSON / Header
- 排查过滤与模板问题

---

## 4. 通知渠道扩展机制

项目目前采用的是一种比较清晰的 **插件式 Notifier 机制**。

### 4.1 抽象基类
文件：

```python
app/notifiers/base.py
```

所有通知渠道都应继承 `BaseNotifier`。

当前约定的核心能力包括：
- `notifier_type`
- `display_name`
- `get_config_schema()`
- `send(...)`
- `test_connection(...)`

这意味着新增渠道时，不需要大改业务主流程，只要按接口实现并注册即可。

---

### 4.2 注册中心
文件：

```python
app/notifiers/registry.py
```

当前机制：
- 通过 `_register(NotifierClass)` 注册渠道
- `get_notifier(type)` 获取对应实例
- `get_all_notifier_types()` 返回前端创建 / 编辑表单所需的 schema

这意味着：
- 前端渠道表单不是写死字段
- 而是根据渠道类返回的 `schema` 动态生成配置表单

这一点非常关键，未来扩展企业微信、飞书时可以直接复用。

---

## 5. 新增通知渠道的标准步骤

下面是未来新增渠道时的推荐流程。

---

### 步骤 1：新增一个 notifier 文件
例如新增企业微信机器人渠道：

```text
app/notifiers/wecom_bot_notifier.py
```

或者新增飞书机器人：

```text
app/notifiers/feishu_bot_notifier.py
```

---

### 步骤 2：继承 BaseNotifier
示意结构：

```python
from app.notifiers.base import BaseNotifier

class WeComBotNotifier(BaseNotifier):
    notifier_type = "wecom_bot"
    display_name = "企业微信机器人"

    @classmethod
    def get_config_schema(cls) -> dict:
        return {
            "webhook_url": {
                "label": "Webhook 地址",
                "type": "text",
                "required": True,
                "placeholder": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
            },
            "mentioned_list": {
                "label": "@成员列表",
                "type": "text",
                "required": False,
                "placeholder": "多个用逗号分隔"
            }
        }

    async def send(self, config: dict, subject: str, body: str, body_format: str = "text", **kwargs):
        ...

    async def test_connection(self, config: dict):
        ...
```

---

### 步骤 3：在 registry 中注册
文件：

```python
app/notifiers/registry.py
```

增加：

```python
from app.notifiers.wecom_bot_notifier import WeComBotNotifier
_register(WeComBotNotifier)
```

如果没有注册：
- 渠道不会出现在创建表单里
- 主流程也无法通过 `get_notifier()` 找到它

---

### 步骤 4：实现 `get_config_schema()`
这是新增渠道最重要的一步之一。

`get_config_schema()` 负责告诉前端：
- 这个渠道有哪些配置项
- 每个字段的展示名称
- 字段类型
- 是否必填
- 占位提示

当前前端页面 `templates/notifiers/form.html` 会根据 schema 动态渲染配置表单。

#### 当前支持的字段类型风格
从现有前端逻辑看，至少兼容：
- `text`
- `password`
- `number`
- `checkbox`

新增字段时建议优先复用这些类型，避免前端还要大改。

---

### 步骤 5：实现 `send()`
`send()` 是真正发送通知的地方。

建议统一行为：
- 输入：`config`, `subject`, `body`, `body_format`, 以及附加上下文
- 输出：布尔成功 / 失败结果，或抛出明确异常

建议在内部处理：
- 参数校验
- 渠道请求封装
- 超时控制
- 错误信息提炼

不要把各种 provider 错误原样乱抛到 UI。

---

### 步骤 6：实现 `test_connection()`
该方法供渠道配置页上的“发送测试”按钮使用。

建议：
- 用最小测试消息发送一次
- 返回 `(ok, msg)` 或兼容当前项目约定的结构
- `msg` 尽量能直接给用户看

例如：
- 成功：`测试消息发送成功`
- 失败：`Webhook 地址无效` / `认证失败` / `请求超时`

---

## 6. 推荐的新渠道设计建议

下面是几个未来高概率扩展的渠道建议。

---

### 6.1 企业微信机器人（WeCom Bot）
#### 推荐 notifier_type
```text
wecom_bot
```

#### 推荐配置字段
- `webhook_url`（必填）
- `mentioned_list`（可选）
- `mentioned_mobile_list`（可选）

#### 发送格式建议
企业微信机器人常见支持：
- text
- markdown

建议先做：
- 优先 text
- 后续视需要扩展 markdown

#### 备注
如果以后要支持“应用消息”而不是“群机器人”，建议单独做新类型，例如：
- `wecom_app`

不要和机器人混在一个 notifier 里，避免配置项过多。

---

### 6.2 飞书机器人（Feishu Bot / Lark Bot）
#### 推荐 notifier_type
```text
feishu_bot
```

#### 推荐配置字段
- `webhook_url`（必填）
- `secret`（可选，如果启用了签名）

#### 发送格式建议
先从最简单的 `text` 开始。
后续如有需要可以支持：
- post
- interactive card

#### 注意事项
如果支持签名校验，需要在 `send()` 中实现时间戳 + 签名逻辑。

---

### 6.3 Telegram Bot
#### 推荐 notifier_type
```text
telegram_bot
```

#### 推荐配置字段
- `bot_token`（必填）
- `chat_id`（必填）
- `parse_mode`（可选，如 Markdown / HTML）
- `disable_notification`（可选 checkbox）

#### 发送格式建议
先支持纯文本。
后续可扩展 Markdown / HTML。

---

### 6.4 Bark
#### 推荐 notifier_type
```text
bark
```

#### 推荐配置字段
- `server_url`（可选，默认官方）
- `device_key`（必填）
- `sound`（可选）
- `group`（可选）
- `icon`（可选）

---

### 6.5 钉钉机器人
#### 推荐 notifier_type
```text
dingtalk_bot
```

#### 推荐配置字段
- `webhook_url`（必填）
- `secret`（可选）

---

## 7. 不同渠道的抽象边界建议

未来渠道越来越多时，最容易出现的问题不是“发不出去”，而是“类型设计混乱”。

### 建议原则

#### 一个 notifier 只做一种配置模型
例如：
- 企业微信机器人 = 一个类型
- 企业微信应用消息 = 另一个类型
- 飞书机器人 = 一个类型
- 飞书应用授权消息 = 另一个类型

不要把完全不同的鉴权模式和发送模型硬塞进同一个 notifier。

#### schema 要稳定
一旦某个 notifier 已投入使用，不要频繁改字段名。
否则旧的 `config_json` 兼容会变麻烦。

#### config_json 要保持可迁移
如果以后 schema 升级，建议：
- 为 config 增加默认值兼容逻辑
- 或增加版本迁移方法

---

## 8. 当前新增渠道对前端的影响

理论上，新增一个 notifier 后，前端主要不需要大改。

原因：
- `notifiers/form.html` 已支持根据 schema 动态渲染配置项
- `notifiers/list.html` 已支持根据 `notifier_type` 展示渠道类型
- `channels/form.html`、`subscriptions/form.html` 会自动列出已存在渠道配置

### 什么时候需要改前端？
只有在以下情况才需要改：

1. 你引入了新的字段类型
   - 例如 file upload / select / textarea / multi-select
2. 你想对某些渠道做专用 UI
   - 比如飞书卡片可视化配置
3. 你想加渠道图标 / 渠道帮助文档入口

否则新增渠道通常是后端实现为主。

---

## 9. 发送主流程说明

核心发送逻辑主要在：

```python
app/services/webhook_processor.py
```

这里会：
- 读取频道配置
- 取模板
- 取 notifier_config
- 渲染模板
- 处理共享订阅 / 自定义收件人
- 获取 notifier 实例
- 调用 notifier.send()
- 写入 NotificationLog

### 这意味着新增渠道时要注意：

#### 1. send() 的入参兼容性
你的 notifier 最好支持统一的调用形式，不要要求上层为某个 provider 特判太多逻辑。

#### 2. 共享通知渠道场景
当前项目支持“共享通知渠道”给其他用户使用。
某些渠道（例如邮箱）允许用户自定义收件人。

未来如果做企业微信 / 飞书，需要先明确：
- 是否允许共享
- 共享时哪些字段可以被订阅用户覆盖
- 是否允许订阅用户自定义目标群 / 成员

建议一开始先保守：
- 共享但不允许订阅用户改关键配置
- 仅允许极少数字段可覆盖

---

## 10. 数据模型说明（新增渠道基本无需改表）

当前新增渠道一般**不需要修改数据库结构**，因为：
- 渠道类型通过 `notifier_type` 区分
- 具体配置通过 `config_json` 存储

这意味着：
- 增加企业微信 / 飞书时，不必新建表
- 只需新加 notifier 实现类

### 只有在以下场景才考虑加表
- 某类渠道配置特别复杂，已经不适合 JSON 存储
- 需要记录 provider 返回的额外状态
- 需要做 OAuth / token 刷新 / 多租户授权

在那之前，优先继续用现有模型。

---

## 11. 错误处理建议

新增渠道时，请统一错误处理风格。

### 推荐做法
- 对外返回简洁、可理解的错误信息
- 记录完整 provider 错误到日志中
- 对用户页面提示不要过度技术化

### 例如
对用户：
- `企业微信发送失败：Webhook 地址无效`
- `飞书发送失败：签名校验失败`
- `Telegram 发送失败：chat_id 不存在`

日志中可保留：
- 原始 HTTP 状态码
- provider 原始响应 body
- 具体请求耗时

---

## 12. 测试建议

每新增一个 notifier，至少验证以下几类场景：

### 基础测试
- 创建渠道配置成功
- 编辑配置成功
- 测试发送成功
- 正常发送成功

### 错误场景
- webhook/token 错误
- 网络超时
- provider 返回 4xx / 5xx
- 缺必填配置

### 模板场景
- 标题为空
- 正文为空
- 长文本
- 特殊字符 / emoji / 中文

### 共享场景（如启用共享）
- 管理员共享成功
- 订阅用户使用共享渠道发送成功
- 自定义覆盖字段逻辑符合预期

---

## 13. 未来建议的演进方向

如果后续渠道变多，建议逐步做以下优化：

### 13.1 把 notifier 文档化
给每个渠道增加：
- 用途说明
- 配置字段说明
- 样例配置
- 常见错误

### 13.2 给 schema 增加更丰富类型
例如：
- `textarea`
- `select`
- `password`
- `url`
- `json`

这样前端动态渲染会更好用。

### 13.3 增加 provider capability 描述
例如某渠道支持：
- text
- markdown
- html
- image
- mentions

以后模板与渠道适配会更智能。

### 13.4 增加渠道级别的发送适配层
例如：
- 某些渠道没有标题概念
- 某些渠道不支持 HTML
- 某些渠道长度有限制

可以在 notifier 内做统一降级策略。

---

## 14. 推荐新增渠道清单（优先级）

如果未来继续拓展，建议优先顺序：

### 第一梯队
1. 企业微信机器人 `wecom_bot`
2. 飞书机器人 `feishu_bot`
3. Telegram Bot `telegram_bot`

### 第二梯队
4. Bark `bark`
5. 钉钉机器人 `dingtalk_bot`
6. Server酱 / PushDeer / ntfy

### 第三梯队
7. 企业微信应用消息
8. 飞书应用授权消息
9. Discord webhook
10. Slack webhook

建议先把“机器人 / webhook 型渠道”做扎实，再考虑 OAuth / 应用授权型渠道。

---

## 15. 新增渠道开发 checklist

以后每加一个新渠道，可以直接照这个清单走：

### 后端
- [ ] 新建 `app/notifiers/xxx_notifier.py`
- [ ] 继承 `BaseNotifier`
- [ ] 定义 `notifier_type`
- [ ] 定义 `display_name`
- [ ] 实现 `get_config_schema()`
- [ ] 实现 `send()`
- [ ] 实现 `test_connection()`
- [ ] 在 `registry.py` 注册

### 联调
- [ ] 渠道出现在“新建通知渠道”页
- [ ] 表单字段可正常渲染
- [ ] 保存配置成功
- [ ] 测试发送成功
- [ ] 实际通知发送成功
- [ ] 发送历史记录正确
- [ ] 错误提示可读

### 共享能力（如需要）
- [ ] 可共享给其他用户
- [ ] 共享用户可正常选择
- [ ] 覆盖字段逻辑正确

---

## 16. 当前结论

这个项目的通知渠道架构已经具备继续扩展的基础。

最大的优点是：
- 有抽象基类
- 有注册中心
- 有动态 schema 表单
- 有统一发送主流程
- 新渠道通常不需要改表结构

这意味着未来扩展企业微信、飞书、Telegram 等渠道时，主要工作量集中在：

1. 新建 notifier 实现类
2. 补 schema
3. 注册到 registry
4. 测试发送与错误处理

而不是整项目推翻重写。

---

## 17. 建议的下一份文档（可选）

如果后续继续维护，建议再补两份文档：

1. `NOTIFIER_API_SPEC.md`
   - 明确 `BaseNotifier` 各方法签名和返回约定

2. `PROVIDER_GUIDES.md`
   - 企业微信 / 飞书 / Telegram / Bark 等接入示例

这样以后不管是你自己扩展，还是让 AI / 别人接手，都会更顺。
