# PROVIDER_GUIDES.md

> NotifyHub 常见通知渠道接入指南。
>
> 用于后续扩展企业微信、飞书、Telegram、Bark、钉钉等通知渠道时参考。

---

## 1. 文档目标

本文档不是通用营销文档，而是面向开发实现。

每个 provider 主要说明：
- 推荐 `notifier_type`
- 推荐配置字段
- 发送格式建议
- 共享能力建议
- 常见错误
- 实现时的注意事项

---

# 2. 企业微信机器人（WeCom Bot）

## 推荐 notifier_type
```text
wecom_bot
```

## 适用场景
- 企业微信群消息推送
- 内部运维提醒
- 任务完成通知
- 监控 / 告警 / 入库通知

## 推荐配置字段
```python
{
    "webhook_url": {
        "type": "text",
        "label": "Webhook 地址",
        "required": True,
        "placeholder": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
    },
    "mentioned_list": {
        "type": "text",
        "label": "@成员列表",
        "required": False,
        "placeholder": "多个用逗号分隔，如 user1,user2"
    },
    "mentioned_mobile_list": {
        "type": "text",
        "label": "@手机号列表",
        "required": False,
        "placeholder": "多个用逗号分隔"
    }
}
```

## 发送格式建议
### 第一阶段
先实现：
- `text`

### 第二阶段（可选）
扩展：
- `markdown`

## send() 适配建议
如果上层给了：
- `subject`
- `body`

推荐合并成：
```text
【标题】
正文
```

## test_connection() 建议
发送一条固定测试消息：
```text
NotifyHub 测试通知
如果你看到这条消息，说明企业微信机器人配置成功。
```

## 共享能力建议
### 建议：可共享，但不允许覆盖 webhook
因为 webhook 一般绑定具体群机器人。

### 可以考虑允许覆盖的字段
- `mentioned_list`
- `mentioned_mobile_list`

但建议默认先不开放，避免复杂度上升。

## 常见错误
- webhook 地址错误
- key 失效
- 机器人被移除
- 消息格式不合法
- markdown 不兼容

## 开发注意事项
- 如果以后支持 markdown，注意企业微信 markdown 能力有限
- 不要假定 HTML 可直接发送
- 如果以后需要群图片 / 文件等，建议做新能力分支，不要塞进第一版

---

# 3. 飞书机器人（Feishu / Lark Bot）

## 推荐 notifier_type
```text
feishu_bot
```

## 适用场景
- 团队通知
- 运维消息
- 自动化任务状态推送
- 系统告警 / 发布通知

## 推荐配置字段
```python
{
    "webhook_url": {
        "type": "text",
        "label": "Webhook 地址",
        "required": True,
        "placeholder": "https://open.feishu.cn/open-apis/bot/v2/hook/..."
    },
    "secret": {
        "type": "password",
        "label": "签名密钥（可选）",
        "required": False,
        "placeholder": "如果机器人启用了签名校验则必填"
    }
}
```

## 发送格式建议
### 第一阶段
先实现：
- `text`

### 第二阶段（可选）
扩展：
- `post`
- `interactive card`

## send() 适配建议
如果存在 `secret`：
- 需要生成时间戳
- 计算签名
- 放入请求体

如果没有 `secret`：
- 直接发送 webhook 请求

## test_connection() 建议
发送简洁测试消息即可，先不要引入复杂 card。

## 共享能力建议
和企业微信类似：
- 建议可共享
- 不允许订阅用户覆盖 webhook / secret

## 常见错误
- webhook 地址错误
- secret 错误
- 签名过期
- 请求 body 结构错误
- 文本过长 / 内容非法

## 开发注意事项
- 飞书的签名逻辑是未来扩展的重点
- 如果以后支持卡片消息，建议单独设计字段，不要让基础版 schema 过大

---

# 4. Telegram Bot

## 推荐 notifier_type
```text
telegram_bot
```

## 适用场景
- 个人通知
- 群组推送
- 自动化脚本结果通知
- 运维告警

## 推荐配置字段
```python
{
    "bot_token": {
        "type": "password",
        "label": "Bot Token",
        "required": True,
        "placeholder": "123456:ABCDEF..."
    },
    "chat_id": {
        "type": "text",
        "label": "Chat ID",
        "required": True,
        "placeholder": "个人或群组 chat_id"
    },
    "parse_mode": {
        "type": "text",
        "label": "Parse Mode",
        "required": False,
        "placeholder": "MarkdownV2 / HTML"
    },
    "disable_notification": {
        "type": "checkbox",
        "label": "静默发送",
        "default": False
    }
}
```

## 发送格式建议
### 第一阶段
支持：
- 纯文本

### 第二阶段
扩展：
- HTML
- MarkdownV2

## send() 适配建议
如果启用 HTML / MarkdownV2：
- 需要处理转义
- 不能直接把任意文本原样当格式文本发出

如果仅文本：
- 最稳

## test_connection() 建议
发送固定测试消息即可。

## 共享能力建议
Telegram 通常不建议共享给多个用户覆盖 `chat_id`，否则语义容易混乱。

### 推荐策略
- 默认不允许共享覆盖 `chat_id`
- 如果要共享，建议做成特殊共享模式

## 常见错误
- bot token 无效
- chat_id 不存在
- bot 没有加入目标群
- parse_mode 格式错误
- MarkdownV2 转义失败

## 开发注意事项
- MarkdownV2 容易踩坑，第一版先不上
- 对于群 / 频道 / 用户 chat_id 不要写死假设

---

# 5. Bark

## 推荐 notifier_type
```text
bark
```

## 适用场景
- iPhone 个人推送
- 简单即时提醒
- 家庭服务器消息
- 自动化任务结果通知

## 推荐配置字段
```python
{
    "server_url": {
        "type": "text",
        "label": "服务地址",
        "required": False,
        "placeholder": "默认 https://api.day.app"
    },
    "device_key": {
        "type": "password",
        "label": "设备 Key",
        "required": True,
        "placeholder": "Bark device key"
    },
    "sound": {
        "type": "text",
        "label": "提示音",
        "required": False,
        "placeholder": "可选"
    },
    "group": {
        "type": "text",
        "label": "分组",
        "required": False,
        "placeholder": "如 NotifyHub"
    },
    "icon": {
        "type": "text",
        "label": "图标 URL",
        "required": False,
        "placeholder": "可选"
    }
}
```

## 发送格式建议
- 以纯文本为主
- 标题和正文天然适配 Bark

## 共享能力建议
一般不建议共享，因为 Bark 更像个人设备推送。

## 常见错误
- device_key 错误
- server_url 不可达
- 自建 Bark 服务异常

## 开发注意事项
- 先兼容官方 server
- 再考虑自定义 Bark server

---

# 6. 钉钉机器人（DingTalk Bot）

## 推荐 notifier_type
```text
dingtalk_bot
```

## 适用场景
- 团队消息推送
- 运维 / 监控群告警
- 自动任务通知

## 推荐配置字段
```python
{
    "webhook_url": {
        "type": "text",
        "label": "Webhook 地址",
        "required": True,
        "placeholder": "https://oapi.dingtalk.com/robot/send?access_token=..."
    },
    "secret": {
        "type": "password",
        "label": "签名密钥（可选）",
        "required": False,
        "placeholder": "如果机器人启用了安全签名则必填"
    }
}
```

## 发送格式建议
### 第一阶段
先做：
- `text`

### 第二阶段（可选）
- markdown

## 共享能力建议
和企业微信 / 飞书类似，建议：
- 可共享
- 但不允许修改 webhook / secret

## 常见错误
- access_token 失效
- 签名错误
- 群机器人被限制

---

# 7. 邮件（Email）

## 当前状态
当前项目已实现。

文件：
```text
app/notifiers/email_notifier.py
```

## notifier_type
```text
email
```

## 当前配置字段
- smtp_host
- smtp_port
- username
- password
- use_ssl
- use_tls
- from_name
- recipients

## 备注
邮件实现可以作为新增渠道的主要参考样板。

特别适合参考：
- `get_config_schema()` 写法
- `test_connection()` 返回 `(bool, str)` 的方式
- 配置解析与布尔字段处理方式

---

# 8. 共享能力设计建议汇总

| 渠道 | 是否适合共享 | 是否建议允许订阅用户覆盖关键目标 |
|---|---|---|
| Email | 可以 | 可考虑允许覆盖收件人 |
| WeCom Bot | 可以 | 不建议覆盖 webhook |
| Feishu Bot | 可以 | 不建议覆盖 webhook |
| Telegram Bot | 谨慎 | 不建议覆盖 chat_id |
| Bark | 不太建议 | 通常不适合 |
| DingTalk Bot | 可以 | 不建议覆盖 webhook |

### 总原则
共享能力要保守处理：
- 核心凭据不允许覆盖
- 订阅用户如果能覆盖，只能覆盖极少数字段

---

# 9. provider 新增优先级建议

## 第一优先级
1. `wecom_bot`
2. `feishu_bot`
3. `telegram_bot`

## 第二优先级
4. `bark`
5. `dingtalk_bot`

## 第三优先级
6. `discord_webhook`
7. `slack_webhook`
8. `ntfy`
9. `pushdeer`
10. `serverchan`

建议先把最常用的 webhook / bot 型渠道做扎实，再考虑 OAuth / 应用授权型集成。

---

# 10. 每个新 provider 的最小交付要求

以后新增一个 provider，建议至少达到以下标准：

- [ ] 能在“新建通知渠道”页创建
- [ ] 能保存配置
- [ ] 能发送测试消息
- [ ] 能在真实 Webhook 流程中发送
- [ ] 失败时错误信息可读
- [ ] 能在发送历史中看到该 notifier_type
- [ ] 文档中有字段说明

---

# 11. 开发建议总结

新增 provider 时，优先做：
- 简单
- 稳定
- 容易调试
- 可测试

不要一上来就追求：
- 复杂富文本
- 交互卡片
- 多态 schema
- 大量 provider 特殊逻辑

第一版原则：

> **先发得出去，再发得漂亮。**

---

# 12. 推荐后续动作

如果以后真的开始加新渠道，建议下一步按这个顺序：

1. 先写 `wecom_bot_notifier.py`
2. 再写 `feishu_bot_notifier.py`
3. 每新增一个，就更新：
   - `registry.py`
   - `DEVELOPMENT.md`
   - 本文档

这样项目的扩展历史会比较干净，不容易失控。
