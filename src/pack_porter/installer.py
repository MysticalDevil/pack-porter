"""下载与安装到 versions/<实例>/mods/。"""

import logging
from pathlib import Path

from . import http
from .errors import ResolveError
from .state import StateStore

log = logging.getLogger(__name__)


class Installer:
    def __init__(self, client, cfg: dict):
        self.client = client
        self.timeout = cfg["modrinth"].get("timeout_seconds", 30)
        self.retries = cfg["modrinth"].get("retries", 3)
        self.cleanup_old = cfg.get("cleanup_old_versions", True)
        self.verify_sha1 = cfg.get("verify_sha1", True)

    def install(self, version_dir, slug: str, resolved, dry_run: bool = False, headers=None) -> str:
        """下载到临时文件并原子改名；校验 sha1；清理旧版；记录状态。

        返回 ``ok`` / ``skipped_exists``；失败抛 :class:`ResolveError`。
        """
        filename = resolved.filename
        url = resolved.url
        sha1 = resolved.sha1
        mods_dir = Path(version_dir) / "mods"
        dest = mods_dir / filename
        state = StateStore(version_dir)

        if self.cleanup_old and not dry_run:
            for old in state.old_files(slug):
                if old != filename:
                    old_path = mods_dir / old
                    if old_path.exists():
                        old_path.unlink()
                        log.info("删除旧版 %s", old_path)

        if dest.exists():
            state.record(slug, filename)
            return "skipped_exists"
        if dry_run:
            return "ok"

        mods_dir.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        try:
            http.download(
                self.client, url, tmp, headers=headers,
                retries=self.retries, timeout=self.timeout,
                expected_sha1=(sha1 if self.verify_sha1 else None),
            )
            tmp.replace(dest)
            state.record(slug, filename)
            return "ok"
        except ResolveError:
            try:
                tmp.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
            raise
        except Exception as exc:  # noqa: BLE001
            try:
                tmp.unlink(missing_ok=True)
            except Exception:  # noqa: BLE001
                pass
            raise ResolveError("download_failed", f"{filename}: {exc}") from exc
