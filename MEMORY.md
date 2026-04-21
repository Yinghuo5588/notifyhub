# MEMORY.md - 长期记忆

> 更新日期：2026-04-21

---

## 👤 用户 & 助手

| 角色 | 信息 |
|------|------|
| 用户 | 图图 / TUTU（`ou_a3fa62a05b1f629c15bd883d121ebe73`，飞书 DM，Asia/Shanghai） |
| 助手 | 小怪 🐾 — 龙虾套橙色小生物，异色瞳（黄+绿） |
| 偏好 | 自然简单沟通，拍板权归用户 |

---

## 📁 已归档项目

| 项目 | 位置 | 说明 |
|------|------|------|
| Emby Next Console | `projects/archives/emby-next-console/` | Emby 管理控制台，v1.0.3 |
| NotifyHub | `projects/archives/notifyhub/` | 通知中心，iOS glassmorphism UI，**已优化UI（5条/页+搜索+7天趋势图），代码推送到 GitHub: Yinghuo5588/notifyhub，2026-04-21归档** |
| Star Office UI | `projects/archives/Star-Office-UI/` | 待部署，3/17 创建，3/30 归档 |
| 音乐热榜同步 | `projects/music-heat-sync/` | 飞书多维表格数据同步 |
| Browser Remote CDP | `projects/archives/openclaw-browser-remote-cdp/` | 浏览器容器远程CDP架构方案（草案），2026-03-16，无实际代码 |
| OpenList-123离线下载 | `projects/archives/oplist-123-offline/` | OpenList→123云盘离线下载桥接，2026-03-17初始化，有git提交，已归档 |

## 📦 活跃项目

| 项目 | 状态 |
|------|------|
| 喵技能菜单系统 | 运行中（`projects/my-skills/`），飞书卡片版 |
| 每日文学经典推送 | 运行中（`literature/classics.md` + `memory/literature-push-state.json`），通过心跳自动推送 |

---

## 🐱 喵技能菜单

| # | 技能 | 快捷用法 |
|---|------|---------|
| 1 | 📡 热榜抓取 | `喵11(5)` 新闻 / `喵12(5)` 音乐 / `喵13(5)` 视频 / `喵14(5)` 社区 / `喵15(5)` 科技 |
| 2 | 🌐 网页助手 | `喵21 关键词` 搜索 / `喵22 URL` 截图 / `喵23 URL` 抓取 / `喵24 URL` 摘要 |
| 3 | 🎤 语音合成 | `喵31 你好` 说话 / `喵32 歌词` 唱歌 / `喵33 智能` 自动风格 |
| 4 | 🌤️ 天气查询 | `喵41 北京` 实时 / `喵42 北京` 预报 / `喵43 北京` 详细 / `喵44 北京` 生活指数 |
| 5 | 📅 日程管理 | `喵51` 今天 / `喵52` 明天 / `喵53 下午3点开会` 建日程 / `喵54 关键词` 搜索 / `喵55` 忙闲 |

**规则：** 喵12(5) = 音乐全平台各5条 / 喵122(5) = 仅QQ音乐5条
**喵33流程：** 识别类型 → 歌词加唱歌前缀 → 逐句音频标签控制
**卡片格式：** turquoise 头 + wide_screen + lark_md + ①②③序号 + **粗体名** + 示例指令
**主菜单：** 带底部跳转按钮（飞书文档链接）
**子分类/平台：** 不带按钮
**热榜结果：** 每条一个按钮跳转原文（截断12字，每行最多3个）
**路由器：** `--json` 输出卡片 JSON，支持 menu/单数字/双数字/完整指令 四种模式
**交互：** `喵`=菜单 → `1~5`=子分类 → 再数字=平台 → 完整指令执行（带按钮跳转）
**详细文档：** [技能多维表格](https://gcnt653bmn1g.feishu.cn/base/C49hbkQIWaRANrsyzUpcFKGvnmf?table=tblZ10Rkcl6ySWEi)

---

## 🔧 API 资源

| 服务 | 端点 |
|------|------|
| 天气 | `https://uapis.cn/api/v1/misc/weather?city=城市名` |
| 热榜 | `https://uapis.cn/api/v1/misc/hotboard?type=平台名` |
| MiMo TTS | `https://api.xiaomimimo.com/v1/chat/completions`（mimo-v2-tts） |

### 飞书多维表格（音乐热榜）
- `app_token: TkKGbPJiIaNZ9LsR85tcKPkYnEg`
- `table_id: tblP2pgqz7oiJ5B0`（原始榜单）

---

## 📚 踩坑速查

> 详细记录在 `.learnings/` 目录（LEARNINGS.md / ERRORS.md）

### 记住这些
- Python 路由顺序：`{param}` 路由放最后
- Vue Layout：用 `<router-view>` 不是 `<slot>`
- Docker 容器内：用 `host.docker.internal`
- Git push 失败：改用 GitHub REST API 逐文件 PUT
- 飞书 TTS：`[音频标签]` 不加 style 时不会被朗读
- 飞书卡片按钮：`value` 不支持嵌套对象（200340），只支持 `url` 跳转
- 飞书卡片按钮回调：需要 HTTP 端点接收，OpenClaw 暂不支持
- 内置 tts 工具：生成 0 字节空文件，飞书发不出去
- MiMo TTS：可用，需 `MIMO_API_KEY` 环境变量（在 .bashrc，exec 不继承需手动 export）
- 飞书卡片含中文引号（""）会解析失败，需转义或替换为普通引号
- `message` 工具 `card` 参数必须是 JSON 对象，不能是字符串
- **浏览器宽屏截图：** Puppeteer 直连 `browser:9222`，`setViewport(1920,1080)`，保存到 `/home/node/clawd/`（message 允许目录）
- **browserless 容器：** `DEFAULT_LAUNCH_ARGS` 环境变量不生效，Tab 频繁断连，别折腾容器配置，直接用 Puppeteer
- **Bing 中国版：** 不加载背景图（Bing 策略），不是浏览器问题

---

## ⏰ 定时任务

| 时间 | 任务 | 行为 |
|------|------|------|
| 21:00 | 每日自检 | 分析日报 → 总结规律/踩坑/经验 → 发报告（不自动修改，但自我沉淀） |
| 21:30 | 待办清单 | 列出可优化点（用户拍板后执行） |

---

## 🧠 记忆分级体系（配合 self-improvement 技能）

所有经验/错误/事件按 `.learnings/SEVERITY.md` 分级：
- `critical` 🔴 → `.learnings/ERRORS.md` → 提升到 SOUL.md
- `high` 🟠 → `.learnings/LEARNINGS.md` → 提升到 TOOLS.md
- `medium` 🟡 → `.learnings/LEARNINGS.md` → 提升到 MEMORY.md
- `low` 🟢 → `memory/日记`（不进 .learnings/）

记录格式遵循 self-improvement 技能标准（LRN/ERR/FEAT 编号 + 状态追踪）。详情见 `.learnings/SEVERITY.md`。

## 记忆升级规则

- 出现 **≥3 次**的信息 → 从日记提炼到 MEMORY.md（长期记忆）
- MEMORY.md 里 **连续 30 天没提到**的信息 → 标记"待淘汰"，下次用到再续期
- **反复犯的错** → 从 `.learnings/` 提升到 TOOLS.md 红色提醒
- **反复做的动作** → 从自由发挥变成"工具组合编排"（固定流程）

## 🧠 开发原则

- **功能完整性：** 能看见、能配置、能操作、有反馈
- **拍板权归用户：** 自动优化只分析，不执行
- **删文件前：** 先 grep 全局引用
