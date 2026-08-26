"""按 slug 记录已安装文件，用于旧版清理。"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


class StateStore:
    """每个实例一份状态：``{ "<slug>": ["old.jar", ...] }``。"""

    def __init__(self, version_dir):
        self.path = Path(version_dir) / ".pack-porter-installed.json"
        self.data: dict = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            return
        try:
            self.data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            log.warning("状态文件损坏，已重置：%s", self.path)
            self.data = {}

    def old_files(self, slug: str) -> list[str]:
        return list(self.data.get(slug, []))

    def record(self, slug: str, filename: str):
        self.data[slug] = [filename]
        self._save()

    def _save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(
                json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as exc:  # noqa: BLE001
            log.warning("写入状态文件失败：%s", exc)
