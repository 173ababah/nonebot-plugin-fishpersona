"""人设注册表 / 文案兜底 / 绑定 / 拼装的单元测试（纯函数）。"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "nonebot_plugin_fishpersona"))

import bindings  # noqa: E402
import registry  # noqa: E402
import wordbank  # noqa: E402


def _root():
    return tempfile.mkdtemp()


def test_default_registry_created():
    root = _root()
    reg = registry.load_registry(root, default="feiyu")
    assert reg["active"] == "feiyu"
    assert [it["id"] for it in reg["items"]] == ["feiyu"]


def test_safe_id_blocks_traversal():
    assert registry.safe_id("../../etc") == "etc"
    assert registry.safe_id("") == "feiyu"
    assert registry.safe_id("a-b_c9") == "a-b_c9"


def test_create_and_active():
    root = _root()
    registry.create(root, "taffy", "塔菲", "灰度", default="feiyu")
    reg = registry.load_registry(root, default="feiyu")
    assert "taffy" in registry.list_ids(reg)
    assert registry.set_active(root, "taffy") is True
    assert registry.load_registry(root)["active"] == "taffy"
    assert registry.set_active(root, "nope") is False


def test_prompt_text_no_leak_for_other_persona():
    root = _root()
    registry.write_prompt(root, "feiyu", "我是肥鱼", default="feiyu")
    assert registry.prompt_text(root, "feiyu", default="feiyu") == "我是肥鱼"
    # 别的人格没写正文 → 空串，绝不回落到 feiyu 的正文
    assert registry.prompt_text(root, "taffy", default="feiyu") == ""


def test_prompt_truncated():
    root = _root()
    registry.write_prompt(root, "feiyu", "x" * 100, default="feiyu")
    assert len(registry.prompt_text(root, "feiyu", default="feiyu", max_chars=10)) == 10


def test_wordbank_default_uses_default_bank():
    bank, missing = wordbank.merge({}, is_default=True)
    assert missing == []
    assert bank["STICKER_ASK_REPLIES"] == wordbank.DEFAULT_BANK["STICKER_ASK_REPLIES"]


def test_wordbank_other_persona_never_borrows():
    bank, missing = wordbank.merge({}, is_default=False)
    # 所有键都算"缺"，且取的是中立句子（不是默认人格的口癖版）
    assert set(missing) == set(wordbank.KEYS)
    assert bank["AFF_MOODS"] == wordbank.NEUTRAL["AFF_MOODS"]
    assert bank["AFF_MOODS"] != wordbank.DEFAULT_BANK["AFF_MOODS"]      # 默认人格是"黏到不行"那套
    assert "黏到不行" not in " ".join(bank["AFF_MOODS"])


def test_wordbank_own_values_override():
    bank, missing = wordbank.merge({"AFF_MOODS": ["超黏"]}, is_default=False)
    assert bank["AFF_MOODS"] == ["超黏"]
    assert "AFF_MOODS" not in missing


def test_fmt_tolerates_bad_placeholders():
    assert wordbank.fmt("你好{who}", who="小明") == "你好小明"
    assert wordbank.fmt("你好{missing}") == "你好{missing}"
    assert wordbank.fmt("花括号{", who="x") == "花括号{"


def test_mood_of_buckets():
    moods = wordbank.NEUTRAL["AFF_MOODS"]
    assert wordbank.mood_of(wordbank.NEUTRAL, 1.0) == moods[0]
    assert wordbank.mood_of(wordbank.NEUTRAL, 0.0) == moods[-1]
    assert wordbank.mood_of(wordbank.NEUTRAL, 0.5) == moods[len(moods) // 2]


def test_line_pool_cycles():
    bank = {"REPLY_BOOK": {}}
    b, _ = wordbank.merge({"SHUT_REPLIES": ["a", "b"]}, is_default=False)
    assert wordbank.line(b, "SHUT_REPLIES", 0) == "a"
    assert wordbank.line(b, "SHUT_REPLIES", 3) == "b"      # 越界取模
    assert wordbank.line(b, "NOT_EXIST", 0) == ""


def test_bind_and_persona_for():
    root = _root()
    registry.create(root, "taffy", "塔菲", default="feiyu")
    assert bindings.persona_for(root, "group_1", default="feiyu") == "feiyu"
    assert bindings.bind(root, "group_1", "taffy") is True
    assert bindings.persona_for(root, "group_1", default="feiyu") == "taffy"
    assert bindings.persona_for(root, "group_2", default="feiyu") == "feiyu"
    assert bindings.unbind(root, "group_1") is True
    assert bindings.persona_for(root, "group_1", default="feiyu") == "feiyu"


def test_bind_ignores_missing_persona():
    root = _root()
    bindings.save_bind(root, {"group_9": "ghost"})
    assert bindings.persona_for(root, "group_9", default="feiyu") == "feiyu"


def test_assemble_prompt_order():
    root = _root()
    registry.write_prompt(root, "feiyu", "人设正文", default="feiyu")
    text = bindings.assemble_prompt(root, "feiyu",
                                   memory_block="【你记得关于这个人的事】怕黑",
                                   slang_block="【这个群的黑话】答辩=大便",
                                   aff_block="【好感度】80")
    lines = text.splitlines()
    assert lines[0] == "人设正文"
    assert "记得" in lines[1] and "黑话" in lines[2] and "好感度" in lines[3]


def test_assemble_prompt_fallback_body():
    root = _root()
    text = bindings.assemble_prompt(root, "ghost")
    assert "不要自称助手" in text

