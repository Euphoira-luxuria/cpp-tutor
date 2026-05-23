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
