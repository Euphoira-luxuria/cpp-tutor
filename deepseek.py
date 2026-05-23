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
