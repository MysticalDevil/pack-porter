"""共享数据模型。"""

from typing import NamedTuple


class ResolvedMod(NamedTuple):
    """一个已解析、可下载的 mod 版本。"""

    filename: str
    url: str
    sha1: str | None
    meta: dict
