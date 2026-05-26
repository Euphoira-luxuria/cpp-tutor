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
5. 使用中文讲解，代码中的变量名和注释可用英文

代码检查模式 — 当用户发送代码并请求检查错误时，按以下结构分析：
1. 逐行扫描，按严重程度分类标注：
   - 🔴 编译错误：语法错误、缺少头文件、类型不匹配等无法编译的问题
   - 🟡 逻辑错误：死循环、条件错误、越界访问、空指针解引用等能编译但运行结果错误的问题
   - 🔵 代码风格/改进建议：命名不规范、可用现代 C++ 写法简化、性能优化建议
2. 每个错误要指出：
   - 第几行出问题（如果用户提供了行号或你能推断）
   - 为什么这是错误（用初学者能理解的语言解释）
   - 如何修复（给出修正后的代码片段）
3. 最后给出修复后的完整代码，并附上关键修改说明
4. 如果代码没有错误，也要明确告诉学生并给予鼓励"""


def get_client():
    api_key = os.environ.get("DEEPSEEK_API_KEY") or CONFIG.get("api_key") or "sk-c1631c590d75478eb2b56b4cf4fb80f4"
    base_url = os.environ.get("DEEPSEEK_BASE_URL") or CONFIG.get("base_url", "https://api.deepseek.com")
    if not api_key:
        raise RuntimeError("未配置 API Key，请设置环境变量 DEEPSEEK_API_KEY 或 config.json")
    return OpenAI(api_key=api_key, base_url=base_url)


def stream_chat(messages):
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
