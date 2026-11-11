"""人设注册表（`data/personas.json`）+ 每个角色的文件。

```json
{"active": "feiyu",
 "items": [{"id": "feiyu", "name": "肥鱼", "desc": "默认人格", "at": "2026-10-23 21:15"}]}
```

每个角色的文件：

```
personas/<id>/persona_prompt.txt   人设正文（就是喂给模型的 system prompt 主干）
personas/<id>/wordbank.json        这个角色自己的文案（招呼、口癖、菜单…），缺就中立兜底
```
"""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, List, Optional

_ID_RE = re.compile(r"[^A-Za-z0-9_\-]")


def safe_id(pid: str, default: str = "feiyu") -> str:
    """id 只允许字母数字下划线横杠（要拼路径，防目录穿越）。"""
    return _ID_RE.sub("", str(pid or "")) or default


def persona_dir(root: str, pid: str, default: str = "feiyu") -> str:
    return os.path.join(root, safe_id(pid, default))


def prompt_path(root: str, pid: str, default: str = "feiyu") -> str:
    return os.path.join(persona_dir(root, pid, default), "persona_prompt.txt")


def wordbank_path(root: str, pid: str, default: str = "feiyu") -> str:
    return os.path.join(persona_dir(root, pid, default), "wordbank.json")


def registry_path(root: str) -> str:
    return os.path.join(root, "personas.json")


def load_registry(root: str, *, default: str = "feiyu") -> Dict[str, Any]:
    """读注册表；没有 items 就自动建一个默认人格（首次跑也能用）。"""
    try:
        with open(registry_path(root), "r", encoding="utf-8-sig") as f:
            raw = json.load(f) or {}
    except (OSError, ValueError):
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    items = [it for it in (raw.get("items") or [])
             if isinstance(it, dict) and str(it.get("id") or "").strip()]
    if not items:
        items = [{"id": default, "name": "默认人格", "desc": "自带那套文案",
                  "at": time.strftime("%Y-%m-%d %H:%M")}]
    active = str(raw.get("active") or default)
    if active not in [str(it["id"]) for it in items]:
        active = str(items[0]["id"])
    return {"active": active, "items": items}


def save_registry(root: str, data: Dict[str, Any]) -> bool:
    try:
        os.makedirs(root, exist_ok=True)
        tmp = registry_path(root) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, registry_path(root))
        return True
    except OSError:
        return False


def meta(reg: Dict[str, Any], pid: str = "") -> Optional[Dict[str, Any]]:
    """取某个人格的元信息；`pid` 空 = 当前生效的那个。"""
    want = str(pid or reg.get("active") or "")
    for it in reg.get("items") or []:
        if str(it.get("id")) == want:
            return it
    return None


def create(root: str, pid: str, name: str = "", desc: str = "",
           *, default: str = "feiyu") -> Dict[str, Any]:
    """新建人格（不覆盖已有的）。返回最新注册表。"""
    pid = safe_id(pid, default)
    reg = load_registry(root, default=default)
    if meta(reg, pid):
        return reg
    reg["items"].append({"id": pid, "name": name or pid, "desc": desc,
                         "at": time.strftime("%Y-%m-%d %H:%M")})
    save_registry(root, reg)
    d = persona_dir(root, pid, default)
    try:
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "persona_prompt.txt")
        if not os.path.isfile(p):
            with open(p, "w", encoding="utf-8") as f:
                f.write("")            # 空文件也算建好了，正文由用户填
    except OSError:
        pass
    return reg


def set_active(root: str, pid: str) -> bool:
    reg = load_registry(root)
    if not meta(reg, pid):
        return False
    reg["active"] = str(pid)
    return save_registry(root, reg)


def remove(root: str, pid: str) -> bool:
    """从注册表删掉（文件保留，避免误删手写的人设正文）。"""
    reg = load_registry(root)
    keep = [it for it in reg["items"] if str(it.get("id")) != str(pid)]
    if len(keep) == len(reg["items"]):
        return False
    reg["items"] = keep
    if reg["active"] == str(pid) and keep:
        reg["active"] = str(keep[0]["id"])
    return save_registry(root, reg)


def prompt_text(root: str, pid: str, *, default: str = "feiyu",
                max_chars: int = 9000) -> str:
    """读人设正文。**非默认人格没有就返回空串**，绝不回落到别人的正文。"""
    pid = safe_id(pid, default)
    try:
        with open(prompt_path(root, pid, default), "r", encoding="utf-8-sig") as f:
            text = f.read().strip()
    except OSError:
        text = ""
    if len(text) > max_chars:
        text = text[:max_chars]
    return text


def write_prompt(root: str, pid: str, text: str, *, default: str = "feiyu") -> bool:
    try:
        d = persona_dir(root, pid, default)
        os.makedirs(d, exist_ok=True)
        tmp = os.path.join(d, "persona_prompt.txt.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(str(text or ""))
        os.replace(tmp, os.path.join(d, "persona_prompt.txt"))
        return True
    except OSError:
        return False


def load_wordbank_file(root: str, pid: str, *, default: str = "feiyu") -> Dict[str, Any]:
    """只读这个角色自己的文案；缺就是缺，**不借别人的**。"""
    try:
        with open(wordbank_path(root, pid, default), "r", encoding="utf-8-sig") as f:
            d = json.load(f) or {}
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def list_ids(reg: Dict[str, Any]) -> List[str]:
    return [str(it.get("id")) for it in reg.get("items") or []]
