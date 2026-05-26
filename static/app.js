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
const codeReviewPanel = document.getElementById("code-review-panel");
const codeInput = document.getElementById("code-input");
const toggleReviewBtn = document.getElementById("toggle-review-btn");
const reviewCodeBtn = document.getElementById("review-code-btn");
const closeReviewBtn = document.getElementById("close-review-btn");

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

    // 代码检查面板
    toggleReviewBtn.addEventListener("click", toggleCodeReview);
    closeReviewBtn.addEventListener("click", closeCodeReview);
    reviewCodeBtn.addEventListener("click", reviewCode);
    codeInput.addEventListener("keydown", onCodeInputKeyDown);
    codeInput.addEventListener("input", onCodeInputChange);

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

// ── 代码检查 ──────────────────────────────────────────────

function toggleCodeReview() {
    const show = codeReviewPanel.style.display === "none";
    codeReviewPanel.style.display = show ? "block" : "none";
    toggleReviewBtn.classList.toggle("active", show);
    if (show) {
        codeInput.focus();
        reviewCodeBtn.disabled = !codeInput.value.trim();
    }
}

function closeCodeReview() {
    codeReviewPanel.style.display = "none";
    toggleReviewBtn.classList.remove("active");
    codeInput.value = "";
    reviewCodeBtn.disabled = true;
}

function onCodeInputChange() {
    reviewCodeBtn.disabled = !codeInput.value.trim();
}

function onCodeInputKeyDown(e) {
    if (e.key === "Enter" && e.ctrlKey) {
        e.preventDefault();
        reviewCode();
    }
}

async function reviewCode() {
    const code = codeInput.value.trim();
    if (!code || isStreaming) return;

    const lang = detectCpp(code) ? "cpp" : "";
    const message = `请帮我检查以下 C++ 代码，找出所有错误（编译错误、逻辑错误、内存问题、未定义行为），按严重程度分类标注，并给出修复建议：\n\n\`\`\`${lang}\n${code}\n\`\`\``;

    if (!currentConversationId) {
        await createConversation();
    }

    closeCodeReview();
    reviewCodeBtn.disabled = true;

    isStreaming = true;
    sendBtn.disabled = true;
    reviewCodeBtn.textContent = "检查中...";

    const es = document.getElementById("empty-state");
    if (es) es.remove();

    appendMessage("user", `检查以下 C++ 代码：\n\n\`\`\`${lang}\n${code}\n\`\`\``);

    const aiMsgDiv = appendMessage("assistant", "");
    const bubble = aiMsgDiv.querySelector(".bubble");
    bubble.classList.add("typing-cursor");

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                conversation_id: currentConversationId,
                message: message,
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
                        const conv = conversations.find(c => c.id === currentConversationId);
                        if (conv) { conv.title = data.title; renderSidebar(); }
                    } else if (data.error) {
                        bubble.innerHTML = `<p style="color:#ef4444">${escapeHtml(data.error)}</p>`;
                    }
                } catch (_) {}
            }
        }
    } catch (e) {
        bubble.innerHTML = `<p style="color:#ef4444">网络错误：${escapeHtml(e.message)}</p>`;
    }

    bubble.classList.remove("typing-cursor");
    isStreaming = false;
    sendBtn.disabled = false;
    reviewCodeBtn.textContent = "开始检查";
    reviewCodeBtn.disabled = false;
    codeInput.value = "";
    messageInput.focus();
}

function detectCpp(code) {
    const markers = [
        "#include", "int main", "std::", "cout", "cin", "vector",
        "template", "namespace", "class ", "struct ", "constexpr",
        "nullptr", "auto ", "->", "<<", ">>"
    ];
    return markers.some(m => code.includes(m));
}
