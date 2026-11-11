"""配置（.env 前缀 FISHPERSONA_）。"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Config(BaseModel):
    fishpersona_enabled: bool = Field(default=True, description="总开关")
    fishpersona_root: str = Field(default="", description="人格根目录；留空 = <cwd>/data/personas")
    fishpersona_default: str = Field(default="feiyu", description="默认人格 id")
    fishpersona_max_prompt: int = Field(default=9000, description="人设正文最大字符数（超了截断）")
    fishpersona_leak_default: bool = Field(
        default=False,
        description="非默认人格缺文案时，是否回落到默认人格的句子（默认关，串词比不说话更糟）")
