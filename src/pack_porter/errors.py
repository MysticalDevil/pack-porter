"""解析 / 下载失败的分类。"""


class ResolveError(Exception):
    """版本解析失败；``reason`` 为失败分类码，``message`` 为说明。"""

    def __init__(self, reason: str, message: str = ""):
        self.reason = reason
        self.message = message
        super().__init__(message or reason)
