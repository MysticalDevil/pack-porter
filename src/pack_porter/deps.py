"""Modrinth required 依赖递归解析。"""

import logging

log = logging.getLogger(__name__)


class DependencyResolver:
    """递归解析 Modrinth 版本的 required 依赖（带环检测与深度上限）。"""

    def __init__(self, mr, manifest_slugs: set, max_depth: int = 10):
        self.mr = mr
        self.manifest_slugs = manifest_slugs
        self.max_depth = max_depth
        self.resolved: set = set()
        self.visiting: set = set()
        self._slug_cache: dict = {}

    def collect(self, version_meta: dict, loader: str, mc_version: str) -> list[tuple[str, object]]:
        """收集 version_meta 的 required 依赖（含传递），返回 ``[(slug, ResolvedMod), ...]``。"""
        out: list = []
        self._walk(version_meta, loader, mc_version, out, depth=0)
        return out

    def _walk(self, version_meta, loader, mc_version, out, depth):
        if depth > self.max_depth:
            return
        for project_id in self.mr.required_deps(version_meta):
            slug = self._slug_for(project_id)
            if slug is None:
                continue
            if slug in self.resolved or slug in self.manifest_slugs or slug in self.visiting:
                continue
            self.visiting.add(slug)
            try:
                resolved = self.mr.resolve(slug, loader, mc_version)
                out.append((slug, resolved))
                self._walk(resolved.meta, loader, mc_version, out, depth + 1)
            except Exception as exc:  # noqa: BLE001
                log.warning("依赖 %s 解析失败：%s", slug, exc)
            finally:
                self.visiting.discard(slug)
                self.resolved.add(slug)

    def _slug_for(self, project_id: str):
        if project_id in self._slug_cache:
            return self._slug_cache[project_id]
        proj = self.mr.get_project(project_id)
        slug = (proj or {}).get("slug")
        self._slug_cache[project_id] = slug
        return slug
