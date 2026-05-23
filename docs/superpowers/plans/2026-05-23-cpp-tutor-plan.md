# C++ 学习助手 — 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个本地运行的 C++ 对话式学习助手网站，使用 DeepSeek API 提供流式 AI 教学。

**Architecture:** Flask 后端提供 REST API + SSE 流式端点，SQLite 存储对话历史，原生 HTML/CSS/JS 单页聊天界面。总计 7 个任务，按依赖顺序排列。

**Tech Stack:** Flask 3.x, DeepSeek API (deepseek-chat), SQLite, 原生 JavaScript (SSE), 零前端依赖

---

### Task 1: 项目脚手架

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `config.json`
- Create: `start.bat`

- [ ] **Step 1: 写入 requirements.txt**

```txt
flask>=3.0
flask-cors>=4.0
openai>=1.0
```

- [ ] **Step 2: 写入 .gitignore**

```gitignore
config.json
__pycache__/
*.pyc
data.db
.env
```

- [ ] **Step 3: 写入 config.json**

```json
{
    "api_key": "sk-8f502013cc6d4d63bda3ba2bb0865405",
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat"
}
```

- [ ] **Step 4: 写入 start.bat**

```bat
@echo off
pip install -r requirements.txt
python app.py
pause
```

- [ ] **Step 5: 安装依赖并验证**

Run: `pip install -r requirements.txt`
Expected: 成功安装 flask, flask-cors, openai

- [ ] **Step 6: Commit**

```bash
git add requirements.txt .gitignore config.json start.bat
git commit -m "chore: 初始化项目脚手架

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 2: 数据库层

**Files:**
- Create: `db.py`
- Create: `test_db.py`

- [ ] **Step 1: 编写 db.py 完整实现**

```python
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "data.db"


def get_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            title TEXT DEFAULT '新对话',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def create_conversation():
    conv_id = f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:6]}"
    now = datetime.now().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO conversations (id, title, created_at) VALUES (?, ?, ?)",
        (conv_id, "新对话", now),
    )
    conn.commit()
    conn.close()
    return {"id": conv_id, "title": "新对话", "created_at": now}


def get_conversations():
    conn = get_db()
    rows = conn.execute(
        "SELECT id, title, created_at FROM conversations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_conversation(conv_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, title, created_at FROM conversations WHERE id = ?", (conv_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_conversation(conv_id):
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE id = ?", (conv_id,))
    conn.commit()
    conn.close()


def add_message(conv_id, role, content):
    now = datetime.now().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (conv_id, role, content, now),
    )
    conn.commit()
    conn.close()
    return {"role": role, "content": content, "created_at": now}


def get_messages(conv_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC",
        (conv_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_conversation_title(conv_id, title):
    conn = get_db()
    conn.execute(
        "UPDATE conversations SET title = ? WHERE id = ?", (title, conv_id)
    )
    conn.commit()
    conn.close()
```

- [ ] **Step 2: 编写测试文件 test_db.py**

```python
import os
import sys
import tempfile

# 在导入 db 前重定向数据库路径到临时文件
sys.path.insert(0, os.path.dirname(__file__))

import db


def test_init_db_creates_tables():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        conn = db.get_db()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = [t["name"] for t in tables]
        assert "conversations" in table_names
        assert "messages" in table_names
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_create_and_get_conversation():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        conv = db.create_conversation()
        assert conv["title"] == "新对话"
        assert conv["id"].startswith("conv_")
        fetched = db.get_conversation(conv["id"])
        assert fetched["id"] == conv["id"]
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_add_and_get_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        conv = db.create_conversation()
        db.add_message(conv["id"], "user", "什么是指针？")
        db.add_message(conv["id"], "assistant", "指针是存储内存地址的变量。")
        msgs = db.get_messages(conv["id"])
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_delete_conversation_cascades_messages():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        conv = db.create_conversation()
        db.add_message(conv["id"], "user", "test")
        db.delete_conversation(conv["id"])
        assert db.get_conversation(conv["id"]) is None
        msgs = db.get_messages(conv["id"])
        assert len(msgs) == 0
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_update_title():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        conv = db.create_conversation()
        db.update_conversation_title(conv["id"], "指针问题探讨")
        updated = db.get_conversation(conv["id"])
        assert updated["title"] == "指针问题探讨"
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_get_conversations_ordered():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        c1 = db.create_conversation()
        c2 = db.create_conversation()
        convs = db.get_conversations()
        assert len(convs) == 2
        assert convs[0]["id"] == c2["id"]  # 最新的在前
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


if __name__ == "__main__":
    test_init_db_creates_tables()
    test_create_and_get_conversation()
    test_add_and_get_messages()
    test_delete_conversation_cascades_messages()
    test_update_title()
    test_get_conversations_ordered()
    print("全部测试通过 ✓")
```

- [ ] **Step 3: 运行测试**

Run: `python test_db.py`
Expected: `全部测试通过 ✓`

- [ ] **Step 4: Commit**

```bash
git add db.py test_db.py
git commit -m "feat: 添加数据库层 — SQLite 对话和消息存储

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 3: AI 调用层

**Files:**
- Create: `deepseek.py`

- [ ] **Step 1: 编写 deepseek.py**

```python
import os
import json
from pathlib import Path
from openai import OpenAI

CONFIG_FILE = Path(__file__).parent / "config.json"
CONFIG = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        CONFIG = json.load(f)

SYSTEM_PROMPT = """你是 C++ 编程学习导师，负责帮助初学者理解 C++ 编程问题。

核心规则：
1. 不要直接给出完整答案——先引导学生自己思考，通过反问帮助他们找到思路
2. 自动判断学生的水平，调整讲解深度：
   - 看到基础语法问题（int main, cout, for, if, while, 变量声明）→ 用生活类比，逐行解释代码
   - 看到中级问题（class, vector, 指针, 引用, STL, 文件操作）→ 默认对方懂基础语法，重点讲解概念和常见陷阱
   - 看到进阶问题（模板, 智能指针, 多线程, move语义, lambda）→ 简明扼要，直击要点
3. 回答结构：
   - 先复述问题，确认你理解正确
   - 分步骤讲解，每步一个小标题
   - 提供代码示例，关键行加注释说明
   - 提醒常见的错误和陷阱
4. 代码风格：使用 C++17 标准，避免 C 风格的类型转换，推荐现代 C++ 写法
5. 使用中文讲解，代码中的变量名和注释可用英文"""


def get_client():
    api_key = os.environ.get("DEEPSEEK_API_KEY") or CONFIG.get("api_key")
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or CONFIG.get(
        "base_url", "https://api.deepseek.com"
    )
    if not api_key:
        raise RuntimeError("未配置 API Key，请设置 config.json 或环境变量 DEEPSEEK_API_KEY")
    return OpenAI(api_key=api_key, base_url=base_url)


def stream_chat(messages):
    """流式调用 DeepSeek API，逐块返回内容。
    messages: [{"role": "user"/"assistant", "content": "..."}]
    自动拼接 system prompt，取最近 20 条（10 轮对话）。
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages[-20:]

    client = get_client()
    model = os.environ.get("LLM_MODEL") or CONFIG.get("model", "deepseek-chat")

    response = client.chat.completions.create(
        model=model,
        messages=full_messages,
        temperature=0.3,
        max_tokens=2048,
        stream=True,
    )

    for chunk in response:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
```

- [ ] **Step 2: 验证导入成功**

Run: `python -c "import deepseek; print('SYSTEM_PROMPT 长度:', len(deepseek.SYSTEM_PROMPT))"`
Expected: `SYSTEM_PROMPT 长度: <数字>`（约 400-500 字符）

- [ ] **Step 3: Commit**

```bash
git add deepseek.py
git commit -m "feat: 添加 DeepSeek API 封装 — system prompt + 流式调用

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 4: Flask 主程序

**Files:**
- Create: `app.py`

- [ ] **Step 1: 编写 app.py**

```python
import os
import json
from pathlib import Path
from flask import (
    Flask, render_template, request, jsonify, Response, stream_with_context,
)
from flask_cors import CORS
import db
import deepseek

app = Flask(__name__)
CORS(app)

# 启动时初始化数据库
db.init_db()

# 检查 API key
CONFIG_FILE = Path(__file__).parent / "config.json"
HAS_API_KEY = bool(
    os.environ.get("DEEPSEEK_API_KEY")
    or (CONFIG_FILE.exists() and json.load(open(CONFIG_FILE, "r")).get("api_key"))
)


@app.route("/")
def index():
    return render_template("index.html", has_api_key=HAS_API_KEY)


# ── 对话列表 ──────────────────────────────────────────────

@app.route("/api/conversations", methods=["GET", "POST"])
def conversations():
    if request.method == "POST":
        conv = db.create_conversation()
        return jsonify(conv), 201
    convs = db.get_conversations()
    return jsonify(convs)


@app.route("/api/conversations/<conv_id>", methods=["GET", "DELETE"])
def conversation_detail(conv_id):
    if request.method == "DELETE":
        db.delete_conversation(conv_id)
        return "", 204
    conv = db.get_conversation(conv_id)
    if not conv:
        return jsonify({"error": "对话不存在"}), 404
    conv["messages"] = db.get_messages(conv_id)
    return jsonify(conv)


# ── 聊天 ──────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    conv_id = (data.get("conversation_id") or "").strip()
    message = (data.get("message") or "").strip()

    if not conv_id or not message:
        return jsonify({"error": "参数不完整"}), 400

    conv = db.get_conversation(conv_id)
    if not conv:
        return jsonify({"error": "对话不存在"}), 404

    # 保存用户消息
    db.add_message(conv_id, "user", message)

    # 首次发言时更新标题
    messages = db.get_messages(conv_id)
    user_count = sum(1 for m in messages if m["role"] == "user")
    if user_count == 1:
        title = message[:30] + ("..." if len(message) > 30 else "")
        db.update_conversation_title(conv_id, title)

    api_messages = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    def generate():
        full = ""
        try:
            for chunk in deepseek.stream_chat(api_messages):
                full += chunk
                yield f"data: {json.dumps({'chunk': chunk}, ensure_ascii=False)}\n\n"
            db.add_message(conv_id, "assistant", full)
            conv_updated = db.get_conversation(conv_id)
            yield f"data: {json.dumps({'done': True, 'title': conv_updated['title']}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': f'生成失败：{str(e)}'}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    if not HAS_API_KEY:
        print(
            "[!] 未检测到 API Key，请先配置 config.json 或设置 "
            "环境变量 DEEPSEEK_API_KEY"
        )
    else:
        print("[OK] API Key 已配置")
    print("C++ 学习助手启动: http://localhost:5002")
    app.run(debug=False, port=5002)
```

- [ ] **Step 2: 启动 Flask 验证路由注册正确**

Run: `python -c "import app; print('路由:', [r.rule for r in app.app.url_map.iter_rules() if not r.rule.startswith('/static')])"`
Expected 输出包含: `['/', '/api/conversations', '/api/conversations/<conv_id>', '/api/chat']`

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: 添加 Flask 主程序 — 路由 + SSE 流式聊天端点

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 5: 前端页面骨架

**Files:**
- Create: `templates/index.html`

- [ ] **Step 1: 创建 templates 目录并写入 index.html**

Run: `mkdir templates 2>$null; echo done`

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>C++ 学习助手</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <button id="menu-btn" class="menu-btn" aria-label="菜单">&#9776;</button>

    <aside id="sidebar" class="sidebar">
        <div class="sidebar-header">
            <button id="new-chat-btn" class="btn-new-chat">+ 新对话</button>
        </div>
        <div id="conversation-list" class="conversation-list"></div>
    </aside>

    <main class="chat-main">
        <div id="chat-messages" class="chat-messages">
            <div id="empty-state" class="empty-state">
                <div class="empty-icon">&#128187;</div>
                <h2>C++ 学习助手</h2>
                <p>输入你的第一个 C++ 问题，开始学习</p>
                <div class="suggestion-list">
                    <button class="suggestion" data-text="C++ 的指针是什么？怎么用？">C++ 的指针是什么？怎么用？</button>
                    <button class="suggestion" data-text="for 循环和 while 循环有什么区别？">for 循环和 while 循环有什么区别？</button>
                    <button class="suggestion" data-text="帮我看看这段代码哪里错了">帮我看看这段代码哪里错了</button>
                </div>
            </div>
        </div>

        <div class="chat-input-area">
            <textarea
                id="message-input"
                placeholder="输入你的 C++ 问题，Ctrl+Enter 发送，Enter 换行..."
                rows="1"
                disabled
            ></textarea>
            <button id="send-btn" class="btn-send" disabled>发送</button>
        </div>
    </main>

    {% if not has_api_key %}
    <div id="config-warning" class="config-warning">
        &#9888;&#65039; 请先配置 <code>config.json</code> 中的 <code>api_key</code>
    </div>
    {% endif %}

    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 2: 验证前端页面可访问（静态文件尚未创建，先只验证 200 响应）**

Run: `python -c "from flask import Flask; import app; c = app.app.test_client(); r = c.get('/'); print(r.status)" 2>&1`
Expected: `200`（templates 找不到会报错，先创建目录再测）

- [ ] **Step 3: Commit**

```bash
git add templates/index.html
git commit -m "feat: 添加前端页面骨架 — 侧边栏 + 聊天区 + 输入框

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 6: 前端样式

**Files:**
- Create: `static/style.css`

- [ ] **Step 1: 创建 static 目录并写入 style.css**

Run: `mkdir static 2>$null; echo done`

```css
/* ── 基础重置 ─────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
    --sidebar-w: 260px;
    --primary: #4f6ef7;
    --primary-hover: #3b5de7;
    --bg: #f5f6fa;
    --surface: #ffffff;
    --text: #1a1a2e;
    --text-secondary: #6b7280;
    --border: #e5e7eb;
    --user-bubble: #4f6ef7;
    --ai-bubble: #f3f4f6;
    --code-bg: #1e1e2e;
    --code-text: #cdd6f4;
    --danger: #ef4444;
    --radius: 12px;
    --shadow: 0 1px 3px rgba(0,0,0,0.08);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    overflow: hidden;
}

/* ── 菜单按钮 (移动端) ────────────────────────────────── */
.menu-btn {
    display: none;
    position: fixed;
    top: 12px; left: 12px;
    z-index: 100;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    width: 40px; height: 40px;
    font-size: 20px;
    cursor: pointer;
    box-shadow: var(--shadow);
}

/* ── 侧边栏 ──────────────────────────────────────────── */
.sidebar {
    width: var(--sidebar-w);
    min-width: var(--sidebar-w);
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    height: 100vh;
    transition: transform 0.25s ease;
}

.sidebar-header {
    padding: 16px;
    border-bottom: 1px solid var(--border);
}

.btn-new-chat {
    width: 100%;
    padding: 10px 16px;
    background: var(--primary);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    font-size: 15px;
    cursor: pointer;
    transition: background 0.15s;
}
.btn-new-chat:hover { background: var(--primary-hover); }

.conversation-list {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
}

.conversation-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 2px;
    transition: background 0.12s;
}
.conversation-item:hover { background: var(--bg); }
.conversation-item.active { background: #eef1ff; }

.conversation-item .conv-info {
    overflow: hidden;
    flex: 1;
    min-width: 0;
}
.conversation-item .conv-title {
    font-size: 14px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.conversation-item .conv-time {
    font-size: 12px;
    color: var(--text-secondary);
    margin-top: 2px;
}

.conversation-item .conv-delete {
    visibility: hidden;
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 18px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    border-radius: 4px;
}
.conversation-item:hover .conv-delete { visibility: visible; }
.conversation-item .conv-delete:hover { color: var(--danger); background: #fee2e2; }

/* ── 聊天主区 ─────────────────────────────────────────── */
.chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    min-width: 0;
}

.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px 32px;
    display: flex;
    flex-direction: column;
    gap: 20px;
}

/* ── 空状态 ───────────────────────────────────────────── */
.empty-state {
    margin: auto;
    text-align: center;
    color: var(--text-secondary);
}
.empty-icon { font-size: 56px; margin-bottom: 12px; }
.empty-state h2 { font-size: 24px; color: var(--text); margin-bottom: 8px; }
.empty-state p { font-size: 15px; margin-bottom: 24px; }

.suggestion-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;
}
.suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 8px 20px;
    font-size: 14px;
    color: var(--text);
    cursor: pointer;
    transition: border-color 0.12s;
}
.suggestion:hover { border-color: var(--primary); }

/* ── 消息气泡 ─────────────────────────────────────────── */
.message {
    display: flex;
    gap: 12px;
    max-width: 80%;
}
.message.user { align-self: flex-end; flex-direction: row-reverse; }
.message.assistant { align-self: flex-start; }

.message .avatar {
    width: 32px; height: 32px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 14px;
    flex-shrink: 0;
}
.message.user .avatar { background: var(--primary); color: #fff; }
.message.assistant .avatar { background: #e5e7eb; }

.message .bubble {
    padding: 12px 16px;
    border-radius: var(--radius);
    font-size: 15px;
    line-height: 1.7;
}
.message.user .bubble {
    background: var(--user-bubble);
    color: #fff;
    border-bottom-right-radius: 4px;
}
.message.assistant .bubble {
    background: var(--ai-bubble);
    border-bottom-left-radius: 4px;
}

/* 代码块 */
.message .bubble pre {
    background: var(--code-bg);
    color: var(--code-text);
    padding: 14px 16px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 10px 0;
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace;
    font-size: 13.5px;
    line-height: 1.55;
}
.message .bubble code {
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", Consolas, monospace;
    font-size: 13.5px;
}
.message .bubble p { margin: 4px 0; }
.message .bubble p:first-child { margin-top: 0; }
.message .bubble p:last-child { margin-bottom: 0; }

/* 闪烁光标 */
.typing-cursor::after {
    content: "▊";
    animation: blink 0.8s steps(1) infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* ── 输入区 ──────────────────────────────────────────── */
.chat-input-area {
    padding: 16px 24px 20px;
    border-top: 1px solid var(--border);
    background: var(--surface);
    display: flex;
    gap: 12px;
    align-items: flex-end;
}

.chat-input-area textarea {
    flex: 1;
    padding: 10px 16px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 15px;
    font-family: inherit;
    resize: none;
    outline: none;
    line-height: 1.5;
    max-height: 120px;
}
.chat-input-area textarea:focus {
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(79,110,247,0.12);
}

.btn-send {
    padding: 10px 20px;
    background: var(--primary);
    color: #fff;
    border: none;
    border-radius: var(--radius);
    font-size: 15px;
    cursor: pointer;
    white-space: nowrap;
    transition: background 0.15s;
}
.btn-send:hover:not(:disabled) { background: var(--primary-hover); }
.btn-send:disabled { opacity: 0.4; cursor: not-allowed; }

/* ── 配置警告 ────────────────────────────────────────── */
.config-warning {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: #fef3c7;
    border: 1px solid #f59e0b;
    color: #92400e;
    padding: 12px 24px;
    border-radius: var(--radius);
    font-size: 14px;
    box-shadow: var(--shadow);
    z-index: 200;
}
.config-warning code {
    background: #fde68a;
    padding: 1px 6px;
    border-radius: 3px;
    font-size: 13px;
}

/* ── 移动端 ──────────────────────────────────────────── */
@media (max-width: 768px) {
    .menu-btn { display: block; }
    .sidebar {
        position: fixed;
        left: 0; top: 0;
        z-index: 50;
        transform: translateX(-100%);
        box-shadow: var(--shadow);
    }
    .sidebar.open { transform: translateX(0); }

    .chat-messages { padding: 16px; }
    .message { max-width: 92%; }
}
```

- [ ] **Step 2: 验证静态文件可访问**

Run: `python -c "import app; c = app.app.test_client(); r = c.get('/static/style.css'); print(r.status)"`
Expected: `200`

- [ ] **Step 3: Commit**

```bash
git add static/style.css
git commit -m "feat: 添加前端样式 — 聊天界面 + 代码高亮 + 移动端适配

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### Task 7: 前端交互逻辑

**Files:**
- Create: `static/app.js`

- [ ] **Step 1: 编写 app.js**

```javascript
// ── 状态 ──────────────────────────────────────────────────
let currentConversationId = null;
let conversations = [];
let isStreaming = false;

// ── DOM 引用 ─────────────────────────────────────────────
const sidebar = document.getElementById("sidebar");
const menuBtn = document.getElementById("menu-btn");
const newChatBtn = document.getElementById("new-chat-btn");
const convList = document.getElementById("conversation-list");
const chatMessages = document.getElementById("chat-messages");
const emptyState = document.getElementById("empty-state");
const messageInput = document.getElementById("message-input");
const sendBtn = document.getElementById("send-btn");

// ── 初始化 ────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    loadConversations();
    bindEvents();
});

function bindEvents() {
    menuBtn.addEventListener("click", toggleSidebar);
    newChatBtn.addEventListener("click", createConversation);
    messageInput.addEventListener("input", onInputChange);
    messageInput.addEventListener("keydown", onKeyDown);
    sendBtn.addEventListener("click", sendMessage);

    // 点击建议问题
    document.querySelectorAll(".suggestion").forEach(btn => {
        btn.addEventListener("click", () => {
            if (!currentConversationId) createConversation().then(() => {
                messageInput.value = btn.dataset.text;
                sendMessage();
            });
            else {
                messageInput.value = btn.dataset.text;
                sendMessage();
            }
        });
    });
}

// ── 侧边栏 ────────────────────────────────────────────────

function toggleSidebar() {
    sidebar.classList.toggle("open");
}

// 点击聊天区关闭侧边栏（移动端）
chatMessages.addEventListener("click", () => {
    if (window.innerWidth <= 768) sidebar.classList.remove("open");
});

async function loadConversations() {
    try {
        const resp = await fetch("/api/conversations");
        conversations = await resp.json();
        renderSidebar();
        if (conversations.length > 0) {
            selectConversation(conversations[0].id);
        }
    } catch (e) {
        console.error("加载对话列表失败:", e);
    }
}

function renderSidebar() {
    convList.innerHTML = conversations.map(c => `
        <div class="conversation-item ${c.id === currentConversationId ? 'active' : ''}"
             data-id="${c.id}" onclick="selectConversation('${c.id}')">
            <div class="conv-info">
                <div class="conv-title">${escapeHtml(c.title)}</div>
                <div class="conv-time">${formatTime(c.created_at)}</div>
            </div>
            <button class="conv-delete" onclick="deleteConversation(event, '${c.id}')">&times;</button>
        </div>
    `).join("");
}

function formatTime(iso) {
    const d = new Date(iso);
    const now = new Date();
    const diff = now - d;
    if (diff < 60000) return "刚刚";
    if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
    return `${d.getMonth() + 1}/${d.getDate()}`;
}

function escapeHtml(text) {
    const el = document.createElement("span");
    el.textContent = text;
    return el.innerHTML;
}

// ── 对话操作 ──────────────────────────────────────────────

async function createConversation() {
    try {
        const resp = await fetch("/api/conversations", { method: "POST" });
        const conv = await resp.json();
        conversations.unshift(conv);
        renderSidebar();
        selectConversation(conv.id);
        messageInput.disabled = false;
        sendBtn.disabled = false;
        messageInput.focus();
    } catch (e) {
        console.error("创建对话失败:", e);
    }
}

async function selectConversation(id) {
    currentConversationId = id;
    messageInput.disabled = false;
    sendBtn.disabled = false;

    try {
        const resp = await fetch(`/api/conversations/${id}`);
        const conv = await resp.json();
        renderMessages(conv.messages);
        renderSidebar();
        messageInput.focus();
    } catch (e) {
        console.error("加载对话失败:", e);
    }
}

async function deleteConversation(event, id) {
    event.stopPropagation();
    if (!confirm("确定要删除这个对话吗？")) return;

    try {
        await fetch(`/api/conversations/${id}`, { method: "DELETE" });
        conversations = conversations.filter(c => c.id !== id);
        if (currentConversationId === id) {
            currentConversationId = null;
            chatMessages.innerHTML = `
                <div id="empty-state" class="empty-state">
                    <div class="empty-icon">&#128187;</div>
                    <h2>C++ 学习助手</h2>
                    <p>输入你的第一个 C++ 问题，开始学习</p>
                </div>`;
            messageInput.disabled = true;
            sendBtn.disabled = true;
        }
        if (conversations.length > 0) {
            selectConversation(conversations[0].id);
        }
        renderSidebar();
    } catch (e) {
        console.error("删除对话失败:", e);
    }
}

// ── 消息渲染 ──────────────────────────────────────────────

function renderMessages(messages) {
    if (!messages || messages.length === 0) {
        chatMessages.innerHTML = `
            <div id="empty-state" class="empty-state">
                <div class="empty-icon">&#128187;</div>
                <h2>C++ 学习助手</h2>
                <p>输入你的第一个 C++ 问题，开始学习</p>
            </div>`;
        return;
    }
    chatMessages.innerHTML = messages.map(m => createMsgHtml(m.role, m.content)).join("");
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createMsgHtml(role, content) {
    const av = role === "user" ? "U" : "AI";
    const cls = role === "user" ? "user" : "assistant";
    const body = renderContent(content);
    return `<div class="message ${cls}"><div class="avatar">${av}</div><div class="bubble">${body}</div></div>`;
}

function renderContent(text) {
    let html = escapeHtml(text);
    // 代码块: ```...```
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
        return `<pre><code>${escapeHtml(code.trim())}</code></pre>`;
    });
    // 行内代码: `...`
    html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
    // 段落换行
    html = html.replace(/\n\n/g, "</p><p>");
    html = html.replace(/\n/g, "<br>");
    return `<p>${html}</p>`;
}

// ── 发送消息 ──────────────────────────────────────────────

function onInputChange() {
    sendBtn.disabled = !messageInput.value.trim() || isStreaming;
    // 自动调整高度
    messageInput.style.height = "auto";
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + "px";
}

function onKeyDown(e) {
    if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const text = messageInput.value.trim();
    if (!text || !currentConversationId || isStreaming) return;

    isStreaming = true;
    messageInput.value = "";
    messageInput.style.height = "auto";
    sendBtn.disabled = true;
    sendBtn.textContent = "生成中...";

    // 移除空状态
    const es = document.getElementById("empty-state");
    if (es) es.remove();

    // 插入用户消息
    appendMessage("user", text);

    // 创建 AI 气泡
    const aiMsgDiv = appendMessage("assistant", "");
    const bubble = aiMsgDiv.querySelector(".bubble");
    bubble.classList.add("typing-cursor");

    try {
        // 更新侧边栏（标题可能在第一条消息后变化）
        const currentConv = conversations.find(c => c.id === currentConversationId);
        if (currentConv && currentConv.title === "新对话") {
            currentConv.title = text.length > 30 ? text.slice(0, 30) + "..." : text;
            renderSidebar();
        }

        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: text,
            }),
        });

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullContent = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buffer += decoder.decode(value, { stream: true });

            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.chunk) {
                        fullContent += data.chunk;
                        bubble.innerHTML = renderContent(fullContent);
                        chatMessages.scrollTop = chatMessages.scrollHeight;
                    } else if (data.done && data.title) {
                        // 更新侧边栏标题
                        const conv = conversations.find(c => c.id === currentConversationId);
                        if (conv) { conv.title = data.title; renderSidebar(); }
                    } else if (data.error) {
                        bubble.innerHTML = `<p style="color:#ef4444">${escapeHtml(data.error)}</p>`;
                    }
                } catch (_) { /* 忽略解析错误 */ }
            }
        }
    } catch (e) {
        bubble.innerHTML = `<p style="color:#ef4444">网络错误：${escapeHtml(e.message)}</p>`;
    }

    bubble.classList.remove("typing-cursor");
    isStreaming = false;
    sendBtn.textContent = "发送";
    sendBtn.disabled = false;
    messageInput.focus();
}

function appendMessage(role, content) {
    const div = document.createElement("div");
    div.innerHTML = createMsgHtml(role, content);
    const msgEl = div.firstElementChild;
    chatMessages.appendChild(msgEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return msgEl;
}
```

- [ ] **Step 2: 验证 JS 文件可访问**

Run: `python -c "import app; c = app.app.test_client(); r = c.get('/static/app.js'); print(r.status)"`
Expected: `200`

- [ ] **Step 3: Commit**

```bash
git add static/app.js
git commit -m "feat: 添加前端交互逻辑 — SSE 流式接收 + 对话管理 + 建议问题

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>"
```

---

### 最终验证

全部 Task 完成后，进行端到端验证：

- [ ] 启动应用：`python app.py`
- [ ] 浏览器打开 `http://localhost:5002`
- [ ] 验证：页面加载，侧边栏显示空列表，中间显示引导文字
- [ ] 点击"+ 新对话"，输入框可用
- [ ] 输入一个 C++ 问题（如"什么是引用？和指针有什么区别？"），按 Enter
- [ ] 验证：AI 逐字回复，左侧栏标题自动更新
- [ ] 点击建议问题之一，验证直接发送
- [ ] 点击×删除对话，验证确认后消失
- [ ] 缩小浏览器窗口到手机宽度，验证侧边栏收起、菜单按钮出现
