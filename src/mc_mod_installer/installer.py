"""下载与安装到 versions/<实例>/mods/。"""

import logging
from pathlib import Path

from . import http
from .errors import ResolveError

log = logging.getLogger(__name__)


class Installer:
    def __init__(self, client, cfg: dict):
        self.client = client
        self.timeout = cfg["modrinth"].get("timeout_seconds", 30)
        self.retries = cfg["modrinth"].get("retries", 3)

    def install(self, version_dir, filename: str, url: str, dry_run: bool = False, headers=None) -> str:
        """下载到临时文件并原子改名到 ``version_dir/mods/<filename>``。

        返回 ``ok`` / ``skipped_exists``；下载失败抛 :class:`ResolveError`。
        """
        mods_dir = Path(version_dir) / "mods"
        dest = mods_dir / filename
        if dest.exists():
            return "skipped_exists"
        if dry_run:
            return "ok"

        mods_dir.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        try:
            http.download(self.client, url, tmp, headers=headers, retries=self.retries, timeout=self.timeout)
            tmp.replace(dest)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            try:
                tmp.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
            raise ResolveError("download_failed", f"{filename}: {exc}") from exc
