"""Modrinth API 客户端。"""

import logging

from . import http
from .errors import ResolveError
from .model import ResolvedMod
from .versioning import pick_best

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
        except http.NotFound:
            return None
        # 其它异常（网络/限流）向上抛，由上层归类为 download_failed，不误报「未找到」

    def resolve(self, slug: str, loader: str, mc_version: str) -> ResolvedMod:
        """解析最新可用版本，返回 :class:`ResolvedMod`，或抛 :class:`ResolveError`。"""
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

        chosen = pick_best(candidates, self.priority, key=lambda v: v.get("version_type"))
        if chosen is None:
            raise ResolveError("no_acceptable_type", f"{slug} 无 release/beta/alpha 版本")

        f = self._primary_file(chosen)
        if f is None or not f.get("url"):
            raise ResolveError("download_failed", f"{slug} 无可下载文件")

        filename = f.get("filename") or f"{slug}.jar"
        sha1 = (f.get("hashes") or {}).get("sha1")
        return ResolvedMod(filename=filename, url=f["url"], sha1=sha1, meta=chosen)

    def required_deps(self, version_meta: dict) -> list[str]:
        """返回该版本声明的 required 依赖 project_id 列表。"""
        return [
            d.get("project_id")
            for d in version_meta.get("dependencies", [])
            if d.get("dependency_type") == "required" and d.get("project_id")
        ]

    def _list_versions(self, slug):
        return self._get(f"{self.base}/project/{slug}/version") or []

    @staticmethod
    def _primary_file(version):
        files = version.get("files", [])
        for f in files:
            if f.get("primary"):
                return f
        return files[0] if files else None
