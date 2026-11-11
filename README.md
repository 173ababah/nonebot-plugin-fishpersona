# nonebot-plugin-fishpersona 🐟

> 一个 bot 挂**好几套人设**：注册表 + 每个角色自己的正文与文案库 + **按会话绑定**
> （这个群用 A，那个群用 B，互不干扰）。**零 LLM 开销**，纯文本装配。

从跑了半年的 QQ 机器人（[肥鱼人设](https://github.com/173ababah)）里拆出来的人格层。

## 命令（默认超管）

| 命令 | 说明 |
|------|------|
| `/人格` | 列出所有人格，标出当前会话用的 / 全局的 |
| `/人格 用 taffy` | 全局切人格 |
| `/人格 绑定 taffy` | **只把当前会话**绑到该人格 |
| `/人格 解绑` | 当前会话恢复跟随全局 |
| `/人格 读 taffy` | 看正文（超长截断） |
| `/人格 新建 taffy 塔菲` | 建人格（生成空正文文件） |

## 给别的插件用

```python
from nonebot_plugin_fishpersona import persona_for, assemble_prompt, bank_for

pid  = persona_for(ROOT, session_id)      # 这个会话用谁（绑定 > 全局 > 默认）
sp   = assemble_prompt(ROOT, pid, memory_block=..., slang_block=..., aff_block=...)
bank = bank_for(ROOT, pid)                # 招呼语 / 口癖 / 菜单文案
```

## 最重要的那条规则：**别串词**

| 情况 | 结果 |
|------|------|
| 角色自己的 `wordbank.json` 有 | 用它 |
| 没有，且**就是默认人格** | 用代码里那套原版文案（它本来就是"自带文案"） |
| 没有，且是**别的人格** | 用 `NEUTRAL` 里的**中立句子**，并记一笔"缺" |

一开始图省事让别的人格缺文案时回落默认人格 —— 结果出现"塔菲用肥鱼的语气说话"，
用户一眼就看出来了。**串词比不说话更糟**，所以默认 `FISHPERSONA_LEAK_DEFAULT=false`。
想看缺了哪些键：`bank_for_ex()` 会返回 `missing` 列表。

## 文件结构

```
data/personas/
  personas.json                 {"active": "feiyu", "items": [{id,name,desc,at}]}
  personas_bind.json            {"group_123456": "taffy"}
  feiyu/
    persona_prompt.txt          system prompt 主干
    wordbank.json               这个角色的文案（可缺，缺了中立兜底）
```

## 拼装顺序（别乱调）

```
人设正文
【你记得关于这个人的事】…     ← fishmemory
【这个群的黑话…】…           ← fishslang
【你对{who}的好感度】…        ← 好感度
```

正文**最强**，附加块只是背景数据，所以一律放后面。正文为空时给一句中性开场
（"不要自称助手"），避免模型自由发挥成客服腔。

## 两个实现细节

1. **id 拼路径 → 必须消毒**：`safe_id()` 把非 `[A-Za-z0-9_-]` 全删掉，`../../etc` → `etc`。
2. **`str.format` 会崩**：文案里写了不存在的占位符、或值本身带 `{`，`format` 直接抛异常。
   `fmt()` 统一兜住，返回原文 —— 一条文案不该把整条回复弄挂。

## 测试

```bash
python -m pytest tests -q     # 15 passed
```

覆盖：注册表默认创建/新建/切 active、`safe_id` 防穿越、正文不串、正文截断、
文案中立兜底 vs 默认兜底、自带值覆盖、`fmt` 容错、好感度分档、句子池取模、
绑定优先级与"绑到不存在的人格要忽略"、拼装顺序。

## License

MIT
