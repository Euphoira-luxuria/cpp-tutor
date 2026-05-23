import os
import sys
import tempfile

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


def test_get_conversations_empty():
    """空数据库应返回空列表"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        convs = db.get_conversations()
        assert convs == []
    finally:
        db.DB_PATH = original
        os.unlink(tmp_path)


def test_get_nonexistent_conversation():
    """查询不存在的对话应返回 None"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_path = f.name
    try:
        original = db.DB_PATH
        db.DB_PATH = type(db.DB_PATH)(tmp_path)
        db.init_db()
        result = db.get_conversation("nonexistent_id")
        assert result is None
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
    test_get_conversations_empty()
    test_get_nonexistent_conversation()
    print("全部测试通过")
