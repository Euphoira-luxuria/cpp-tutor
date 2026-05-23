# C++ 学习助手网站 — 设计文档

**日期：** 2026-05-23  
**状态：** 待审阅

---

## 一、项目概述

一个本地运行的 C++ 编程学习助手网站，采用对话式 AI 教学。用户粘贴题目或描述问题，AI 逐步引导解答，而非直接给答案。面向单用户，无需登录。

## 二、技术栈

| 层级 | 技术 | 选型理由 |
|------|------|---------|
| 后端框架 | Flask 3.x | 与现有 copywriter 项目一致，降低认知负担 |
| AI API | DeepSeek (deepseek-chat) | 已有 API key，中文最佳，价格最低 |
| 数据库 | SQLite | 单用户，零配置，文件即数据库 |
| 前端 | 原生 HTML/CSS/JS | 无需构建工具，聊天界面约 300 行 JS |
| 流式输出 | SSE (Server-Sent Events) | 打字机效果，比一次性响应体验好 |
| 部署 | 本地运行 | 单用户 + SQLite，本地运行即可 |

## 三、架构

```
浏览器 (localhost:5002)
  ├── index.html（页面骨架）
  ├── style.css（样式）
  └── app.js（前端逻辑：SSE 接收 + UI 更新）
        │
        ▼ HTTP + SSE
Flask 后端 (app.py)
  ├── /                  → 渲染主页
  ├── /api/chat          → 发送消息（SSE 流式返回）
  ├── /api/conversations → 对话列表 CRUD
  ├── deepseek.py        → AI 调用封装
  └── db.py              → SQLite 操作
```

**文件结构（6 个核心文件）：**
```
cpp-tutor/
├── app.py              # Flask 主入口 + 路由
├── db.py               # 数据库初始化 + 增删查
├── deepseek.py         # DeepSeek 流式调用 + system prompt
├── config.json         # API key（不提交 git）
├── requirements.txt    # flask, flask-cors, openai
├── start.bat           # 一键启动
├── static/
│   ├── style.css
│   └── app.js
└── templates/
    └── index.html
```

## 四、AI 教学行为

### System Prompt 核心

```
你是 C++ 编程导师。核心规则：

1. 不直接给答案——先引导学生思考，反问关键点
2. 自动判定水平（根据题目关键词），调整讲解深度
3. 回答结构：理解问题 → 分步讲解 → 代码示例（带注释） → 常见坑提醒
4. 代码用 C++17 风格，不用 C 风格转换
```

### 水平自适应

| 触发词 | 水平 | 讲解策略 |
|--------|------|---------|
| `int main`、`cout`、`for`、`if`、`while` | 入门 | 生活类比，逐行解释 |
| `class`、`vector`、`指针`、`引用`、`STL` | 中级 | 默认懂语法，重点讲概念 |
| `模板`、`智能指针`、`多线程`、`move`、`lambda` | 进阶 | 简明扼要，直击要点 |

### 对话上下文

每次请求携带：system prompt + 最近 10 轮对话。不传全部历史以节省 token 并保持 AI 注意力。

**API 参数：** temperature=0.3（低温度保证代码和讲解的准确性），max_tokens=2048。

## 五、数据库设计

### conversations

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | TEXT PK | 如 `conv_20250523_a1b2c3` |
| `title` | TEXT | 首条用户消息的前 30 字 |
| `created_at` | TEXT | ISO 时间戳 |

### messages

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | INTEGER PK | 自增 |
| `conversation_id` | TEXT FK | 外键关联 conversations |
| `role` | TEXT | `user` / `assistant` |
| `content` | TEXT | 消息全文 |
| `created_at` | TEXT | ISO 时间戳 |

**操作：** 新建对话 → 发消息时自动更新标题 → 删除对话级联删除消息。

## 六、界面设计

### 桌面端布局

- 左侧 260px 侧边栏：新对话按钮 + 历史对话列表（标题 + 时间），选中高亮
- 右侧聊天区：消息气泡（用户蓝色靠右，AI 灰色靠左），代码块深色背景
- 底部输入区：输入框 + 发送按钮，支持 Ctrl+Enter 快捷键
- AI 回复流式渲染，逐字出现

### 移动端适配

- 侧边栏自动收起，左上角 ☰ 菜单按钮呼出
- 聊天区占满屏幕宽度

### 加载/空状态

- 加载中：顶部进度条
- 无对话：居中引导文字"输入你的第一个 C++ 问题"
- AI 生成中：气泡内闪烁光标提示

## 七、边界情况与错误处理

| 情况 | 处理 |
|------|------|
| API key 未配置 | 启动时打印提示，页面显示配置引导 |
| API 调用失败 | 显示错误消息"生成失败：xxx"，不丢失用户输入 |
| 网络中断 | 前端检测 SSE 断连，自动重试一次 |
| 空消息提交 | 前端禁用发送按钮，后端也做校验 |
| 数据库满/损坏 | 启动时自动创建表（CREATE IF NOT EXISTS） |

## 八、不做的事

- 不做 Markdown 完整渲染——仅处理代码块高亮和段落换行
- 不做多用户/登录系统
- 不做富文本编辑器——纯文本输入
- 不缓存 AI 回复——每次都是实时请求
