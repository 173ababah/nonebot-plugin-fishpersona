"""会话 → 人格 的绑定，以及 system prompt 的拼装。

绑定文件 `data/personas_bind.json`：`{"group_123456": "taffy", "private_789": "feiyu"}`。
没有绑定的会话用注册表里的 `active`。

拼装顺序（顺序有讲究，别乱调）：

```
人设正文
【你记得关于这个人的事】…          ← 记忆（可选，来自 fishmemory）
【这个群的黑话…】…                ← 黑话（可选，来自 fishslang）
【你对{who}的好感度】…            ← 好感度（可选）
```

所有附加块都放在正文**后面**：正文是最强的指令，附加块是"背景数据"。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

try:                        # 包内正常导入
    from . import registry, wordbank
except ImportError:         # 允许当独立模块导入（单测 / 别的脚本直接引用）
    import registry  # type: ignore
    import wordbank  # type: ignore


def bind_path(root: str) -> str:
    return os.path.join(root, "personas_bind.json")


def load_bind(root: str) -> Dict[str, str]:
    try:
        with open(bind_path(root), "r", encoding="utf-8-sig") as f:
            raw = json.load(f) or {}
        return {str(k): str(v) for k, v in raw.items() if str(v).strip()} if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def save_bind(root: str, data: Dict[str, str]) -> bool:
    try:
        os.makedirs(root, exist_ok=True)
        tmp = bind_path(root) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, bind_path(root))
        return True
    except OSError:
        return False


def bind(root: str, chat_key: str, pid: str) -> bool:
    data = load_bind(root)
    data[str(chat_key)] = str(pid)
    return save_bind(root, data)


def unbind(root: str, chat_key: str) -> bool:
    data = load_bind(root)
    if str(chat_key) not in data:
        return False
    data.pop(str(chat_key), None)
    return save_bind(root, data)


def persona_for(root: str, chat_key: str, *, default: str = "feiyu") -> str:
    """这个会话用哪个人格：绑定优先，其次注册表的 active，最后默认。"""
    pid = load_bind(root).get(str(chat_key) or "")
    if pid:
        reg = registry.load_registry(root, default=default)
        if registry.meta(reg, pid):
            return pid
    reg = registry.load_registry(root, default=default)
    return str(reg.get("active") or default)


def assemble_prompt(root: str, pid: str, *, default: str = "feiyu",
                    max_chars: int = 9000,
                    leak_default: bool = False,
                    memory_block: str = "",
                    slang_block: str = "",
                    aff_block: str = "") -> str:
    """拼 system prompt：正文 + 附加块（顺序见模块注释）。"""
    body = registry.prompt_text(root, pid, default=default, max_chars=max_chars)
    extras: List[str] = [b.strip() for b in (memory_block, slang_block, aff_block) if b and b.strip()]
    if not body:
        # 正文空 = 这个角色还没写；给一句中性的开场，避免模型自由发挥
        body = "你是群里的一个角色。说话自然、简短，不要自称助手。"
    return "\n".join([body] + extras)


def bank_for(root: str, pid: str, *, default: str = "feiyu",
             leak_default: bool = False) -> Dict[str, Any]:
    """这个角色生效的文案（含缺失列表，用 `bank_for_ex` 拿）。"""
    bank, _ = bank_for_ex(root, pid, default=default, leak_default=leak_default)
    return bank


def bank_for_ex(root: str, pid: str, *, default: str = "feiyu",
                leak_default: bool = False):
    pid = registry.safe_id(pid, default)
    own = registry.load_wordbank_file(root, pid, default=default)
    is_default = pid == registry.safe_id(default, default)
    return wordbank.merge(own, is_default=is_default, leak_default=leak_default)

