"""Modrinth API 客户端。"""

import logging

from . import http
from .errors import ResolveError

log = logging.getLogger(__name__)


class ModrinthClient:
    def __init__(self, client, cfg: dict):
        self.client = client
        mc = cfg["modrinth"]
        self.base = mc["base_url"]
        self.headers = {"User-Agent": mc["user_agent"]}
        self.timeout = mc.get("timeout_seconds", 30)
        self.retries = mc.get("retries", 3)
        self.delay = mc.get("delay_seconds", 0.3)
        self.priority = cfg.get("version_priority", ["release", "beta", "alpha"])

    def _get(self, url):
        return http.get_json(
            self.client, url, headers=self.headers,
            retries=self.retries, delay=self.delay, timeout=self.timeout,
        )

    def get_project(self, slug_or_id):
        try:
            return self._get(f"{self.base}/project/{slug_or_id}")
        except Exception as exc:  # noqa: BLE001
            log.info("Modrinth 项目不存在：%s（%s）", slug_or_id, exc)
            return None

    def resolve(self, slug: str, loader: str, mc_version: str):
        """返回 ``(filename, url, version_meta)``，或抛 :class:`ResolveError`。"""
        proj = self.get_project(slug)
        if proj is None:
            raise ResolveError("not_found", f"Modrinth 未找到项目 {slug}")

        versions = self._list_versions(slug)
        candidates = [
            v for v in versions
            if loader in v.get("loaders", []) and mc_version in v.get("game_versions", [])
        ]
        if not candidates:
            has_loader = any(loader in v.get("loaders", []) for v in versions)
            has_mc = any(mc_version in v.get("game_versions", []) for v in versions)
            if has_mc and not has_loader:
                raise ResolveError("no_loader", f"{slug} 无 {loader} 版本")
            if has_loader and not has_mc:
                raise ResolveError("no_game_version", f"{slug} 无 {mc_version} 版本")
            raise ResolveError("no_acceptable_type", f"{slug} 无匹配 {mc_version}/{loader} 的版本")

        chosen = self._pick(candidates)
        if chosen is None:
            raise ResolveError("no_acceptable_type", f"{slug} 无 release/beta/alpha 版本")

        f = self._primary_file(chosen)
        if f is None or not f.get("url"):
            raise ResolveError("download_failed", f"{slug} 无可下载文件")

        filename = f.get("filename") or f"{slug}.jar"
        return filename, f["url"], chosen

    def required_deps(self, version_meta: dict) -> list[str]:
        """返回该版本声明的 required 依赖 project_id 列表。"""
        return [
            d.get("project_id")
            for d in version_meta.get("dependencies", [])
            if d.get("dependency_type") == "required" and d.get("project_id")
        ]

    def _list_versions(self, slug):
        try:
            return self._get(f"{self.base}/project/{slug}/version") or []
        except Exception as exc:  # noqa: BLE001
            log.warning("获取 %s 版本列表失败：%s", slug, exc)
            return []

    def _pick(self, candidates):
        for p in self.priority:
            for v in candidates:
                if v.get("version_type") == p:
                    return v
        return None

    @staticmethod
    def _primary_file(version):
        files = version.get("files", [])
        for f in files:
            if f.get("primary"):
                return f
        return files[0] if files else None
