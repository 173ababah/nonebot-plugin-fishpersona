"""每角色的文案库（wordbank）+ 中立兜底 + 占位符格式化。

核心规则（线上总结出来的，**别改成"缺了就借默认人格的"**）：

| 情况 | 结果 |
|------|------|
| 这个角色自己的 `wordbank.json` 有 | 用它 |
| 没有，且**它就是默认人格** | 用代码里那套原版文案（默认人格的"自带文案"） |
| 没有，且是**别的人格** | 用 `NEUTRAL` 里的中立句子，并记一笔"缺" |

为什么：默认人格的句子带着强烈的口癖。别的人格缺文案时借了，就会出现
"塔菲用肥鱼的语气说话" —— 用户一眼看出来，比不说话更糟。

占位符用 `str.format`，值里出现 `{` `}` 会抛异常，所以格式化要 `try/except` 兜住。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional, Tuple

# 代码里那套「默认人格自带文案」（真实项目里比这多，这里保留行为关键的几类）
DEFAULT_BANK: Dict[str, Any] = {
    "CALL_NAMES": ["你"],
    "REPLY_BOOK": {},
    "ADDONS": [],
    "STICKER_ASK_REPLIES": ["喏，给你。"],
    "LINK_FALLBACK": ["这个链接我打不开。"],
    "LINK_EMPTY": ["看不到这个链接的内容。"],
    "MEME_JIE_POOL": ["哦，知道。"],
    "AFF_HOW_LINES": ["多聊聊天就会涨。"],
    "FEED_OK_LINES": ["好。"],
    "FEED_FULL_LINES": ["今天已经够了。"],
    "SHUT_REPLIES": ["好，我不说了。"],
    "AFF_LOW_LINES": ["嗯。"],
    "AFF_HIGH_LINES": ["嗯。"],
    "AFF_MOODS": ["已经黏到不行了", "很喜欢你", "挺喜欢你", "对你印象不错",
                  "没什么特别感觉", "有点烦你", "挺讨厌你的", "非常讨厌你", "讨厌到不想理你"],
    "AFF_BLOCK_FMT": "【你对{who}的好感度】{v}（{mood}，满分{max}，最低{min}）",
    "AFF_BLOCK_HIGH": "：你现在特别黏他，句句都想扯到他身上，但别刷屏。",
    "AFF_BLOCK_LOW": "：你现在有点闹别扭，话变短、语气变淡；不要阴阳怪气、不要损人。",
    "PATRON_BLOCK": ("【背景数据（别主动提）】{who} 是你的金主（累计给了 {sp} 金币），"
                     "对他明显更热情、更给面子，别把「{tier}」挂嘴上，也别主动报金额。"),
    "MENU_TITLE": "指令菜单",
    "MENU_SUBTITLE": "",
    "MENU_FOOT": "",
    "MENU_ITEMS": ["📮 直接 @我|或者私聊，都能聊"],
    "AFF_CARD_TALK": "跟我聊过 {n} 条",
    "AFF_CARD_LOW": "很不待见",
    "AFF_CARD_HIGH": "黏到不行",
    "AFF_CARD_EMPTY": "还在攒印象…",
    "AFF_CARD_BADGE": "好感度",
    "AFF_CARD_MAX": "满级",
}

# 中立兜底：不带任何口癖，谁都能用
NEUTRAL: Dict[str, Any] = {
    "CALL_NAMES": [],
    "REPLY_BOOK": {},
    "ADDONS": [],
    "STICKER_ASK_REPLIES": ["喏，给你。"],
    "LINK_FALLBACK": ["这个链接我打不开。"],
    "LINK_EMPTY": ["看不到这个链接的内容。"],
    "MEME_JIE_POOL": ["哦，知道。"],
    "AFF_HOW_LINES": ["多聊聊天就会涨。"],
    "FEED_OK_LINES": ["好。"],
    "FEED_FULL_LINES": ["今天已经够了。"],
    "SHUT_REPLIES": ["好，我不说了。"],
    "AFF_LOW_LINES": ["嗯。"],
    "AFF_HIGH_LINES": ["嗯。"],
    "AFF_MOODS": ["已经很熟了", "挺喜欢", "还行", "印象一般",
                  "没什么特别感觉", "有点疏远", "不太熟", "很远", "基本不认识"],
    "AFF_BLOCK_FMT": "【你对{who}的好感度】{v}（{mood}，满分{max}，最低{min}）",
    "AFF_BLOCK_HIGH": "：语气热一点。",
    "AFF_BLOCK_LOW": "：语气淡一点，别阴阳怪气。",
    "PATRON_BLOCK": "【背景数据（别主动提）】{who} 累计给了 {sp} 金币。",
    "MENU_TITLE": "指令菜单",
    "MENU_SUBTITLE": "",
    "MENU_FOOT": "",
    "MENU_ITEMS": [],
    "AFF_CARD_TALK": "聊过 {n} 条",
    "AFF_CARD_LOW": "不太熟",
    "AFF_CARD_HIGH": "很熟",
    "AFF_CARD_EMPTY": "还在攒印象…",
    "AFF_CARD_BADGE": "好感度",
    "AFF_CARD_MAX": "满级",
}

KEYS = tuple(NEUTRAL.keys())


def merge(bank: Optional[Dict[str, Any]], *, is_default: bool = False,
          leak_default: bool = False) -> Tuple[Dict[str, Any], List[str]]:
    """合成这个角色实际生效的文案。

    返回 `(文案dict, 缺失的键列表)`。缺失只对非默认人格有意义（默认人格永远有兜底）。
    """
    out: Dict[str, Any] = {}
    missing: List[str] = []
    src = bank if isinstance(bank, dict) else {}
    for key in KEYS:
        val = src.get(key)
        if val in (None, "", [], {}):
            if is_default:
                val = copy.deepcopy(DEFAULT_BANK.get(key, NEUTRAL[key]))
            elif leak_default:
                val = copy.deepcopy(DEFAULT_BANK.get(key, NEUTRAL[key]))
            else:
                val = copy.deepcopy(NEUTRAL[key])
                missing.append(key)
        out[key] = copy.deepcopy(val)
    return out, missing


def pick(bank: Dict[str, Any], key: str, default: Any = "") -> Any:
    return bank.get(key, default)


def fmt(text: str, **kw) -> str:
    """带占位符的句子格式化；**占位符写错/值里有花括号都不能崩**。"""
    if not isinstance(text, str):
        return str(text)
    try:
        return text.format(**kw)
    except (KeyError, IndexError, ValueError):
        return text


def line(bank: Dict[str, Any], key: str, index: int = 0, **kw) -> str:
    """从"句池"里取第 index 条并格式化（池空返回空串）。"""
    pool = bank.get(key) or []
    if not isinstance(pool, (list, tuple)) or not pool:
        return ""
    try:
        v = pool[index % len(pool)]
    except (TypeError, ZeroDivisionError):
        return ""
    return fmt(v, **kw)


def mood_of(bank: Dict[str, Any], ratio: float) -> str:
    """按好感度比例（0~1）从 `AFF_MOODS`（9 档，高→低）里挑一句。"""
    moods = bank.get("AFF_MOODS") or NEUTRAL["AFF_MOODS"]
    if not moods:
        return ""
    ratio = max(0.0, min(1.0, float(ratio)))
    idx = int(round((1.0 - ratio) * (len(moods) - 1)))
    return str(moods[min(len(moods) - 1, max(0, idx))])
