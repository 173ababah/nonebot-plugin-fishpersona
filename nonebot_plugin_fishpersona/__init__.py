"""nonebot-plugin-fishpersona —— 多套人设（registry + 每角色文案 + 会话绑定）。

命令：

| 命令 | 说明 |
|------|------|
| `/人格` | 列出所有人格，标出当前生效的 |
| `/人格 用 <id>` | 把全局生效人格切成 `<id>` |
| `/人格 绑定 <id>` | 只把**当前会话**绑到 `<id>`（群里换人设不动别人） |
| `/人格 解绑` | 当前会话恢复跟随全局 |
| `/人格 读 <id>` | 看这个角色的人设正文（超长只显示开头） |
| `/人格 新建 <id> [名字]` | 建一个人格（会生成空正文文件） |

给别的插件用：

```python
from nonebot_plugin_fishpersona import persona_for, assemble_prompt, bank_for

pid = persona_for(root, session_id)                       # 这个会话用谁
sp  = assemble_prompt(root, pid, memory_block=..., slang_block=...)
bank = bank_for(root, pid)                                # 招呼语/口癖/菜单文案
```
"""

from __future__ import annotations

import os

from nonebot import get_plugin_config, on_command
from nonebot.adapters import Event, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata

from . import bindings, registry
from .config import Config

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-fishpersona",
    description="多套人设：注册表 + 每角色文案库（缺就中立兜底，绝不串词）+ 会话绑定",
    usage="/人格 | /人格 用 <id> | /人格 绑定 <id> | /人格 解绑 | /人格 读 <id> | /人格 新建 <id>",
    type="application",
    config=Config,
    homepage="https://github.com/173ababah/nonebot-plugin-fishpersona",
    supported_adapters={"~onebot.v11"},
)

cfg = get_plugin_config(Config)
ROOT = cfg.fishpersona_root or os.path.join(os.getcwd(), "data", "personas")
DEFAULT = cfg.fishpersona_default

persona_cmd = on_command("人格", aliases={"persona"}, priority=16, block=True,
                         permission=SUPERUSER)


def _chat_key(event: Event) -> str:
    fn = getattr(event, "get_session_id", None)
    if callable(fn):
        try:
            return str(fn())
        except Exception:
            pass
    return ""


@persona_cmd.handle()
async def _(event: Event, arg: Message = CommandArg()):
    if not cfg.fishpersona_enabled:
        await persona_cmd.finish("人设功能关着呢（FISHPERSONA_ENABLED=false）")
    text = arg.extract_plain_text().strip()
    reg = registry.load_registry(ROOT, default=DEFAULT)
    chat = _chat_key(event)

    if not text:
        cur = bindings.persona_for(ROOT, chat, default=DEFAULT)
        lines = ["共 %d 个人格（会话绑定的优先）：" % len(reg["items"])]
        for it in reg["items"]:
            pid = str(it.get("id"))
            mark = " ← 当前" if pid == cur else (" ← 全局" if pid == reg["active"] else "")
            body = registry.prompt_text(ROOT, pid, default=DEFAULT) if False else ""
            lines.append("· %s（%s）%s%s" % (pid, it.get("name") or pid,
                                             (it.get("desc") or ""), mark))
        lines.append("本会话：%s；全局：%s" % (cur, reg["active"]))
        await persona_cmd.finish("\n".join(lines))

    action, _, rest = text.partition(" ")
    action = action.strip()
    arg1 = rest.strip()

    if action in ("用", "use"):
        if not registry.set_active(ROOT, arg1):
            await persona_cmd.finish("没有这个人格：%s" % arg1)
        await persona_cmd.finish("全局人格已切成「%s」" % arg1)

    if action in ("绑定", "bind"):
        if not registry.meta(reg, arg1):
            await persona_cmd.finish("没有这个人格：%s" % arg1)
        if not chat:
            await persona_cmd.finish("认不出这个会话…")
        bindings.bind(ROOT, chat, arg1)
        await persona_cmd.finish("这个会话以后用「%s」" % arg1)

    if action in ("解绑", "unbind"):
        ok = bindings.unbind(ROOT, chat)
        await persona_cmd.finish("已解绑，恢复跟随全局" if ok else "本来就没绑定")

    if action in ("读", "read", "看"):
        pid = arg1 or bindings.persona_for(ROOT, chat, default=DEFAULT)
        body = registry.prompt_text(ROOT, pid, default=DEFAULT)
        if not body:
            await persona_cmd.finish("「%s」还没有正文（persona_prompt.txt 是空的）" % pid)
        await persona_cmd.finish("「%s」正文 %d 字：\n%s" %
                                 (pid, len(body), body[:300] + ("…" if len(body) > 300 else "")))

    if action in ("新建", "new", "add"):
        parts = arg1.split()
        if not parts:
            await persona_cmd.finish("用法：/人格 新建 <id> [名字]")
        pid = parts[0]
        name = " ".join(parts[1:]) or pid
        before = len(reg["items"])
        registry.create(ROOT, pid, name, default=DEFAULT)
        after = registry.load_registry(ROOT, default=DEFAULT)
        if len(after["items"]) == before:
            await persona_cmd.finish("「%s」已经存在" % pid)
        await persona_cmd.finish("建好了「%s」；正文写进 %s" %
                                 (pid, registry.prompt_path(ROOT, pid, DEFAULT)))

    await persona_cmd.finish("用法：/人格 | /人格 用 <id> | /人格 绑定 <id> | /人格 解绑 | /人格 读 <id> | /人格 新建 <id>")
