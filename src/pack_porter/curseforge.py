"""CurseForge API 客户端（仅 source=curseforge 的条目）。"""

import logging

from . import http
from .errors import ResolveError
from .model import ResolvedMod
from .versioning import pick_best

log = logging.getLogger(__name__)

LOADER_TYPE = {"any": 0, "forge": 1, "fabric": 4, "neoforge": 6}
RELEASE_TYPE = {"release": 1, "beta": 2, "alpha": 3}
RELEASE_NAME = {v: k for k, v in RELEASE_TYPE.items()}


class CurseForgeClient:
    def __init__(self, client, cfg: dict, api_key: str):
        self.client = client
        self.api_key = api_key
        cc = cfg["curseforge_api"]
        self.base = cc["base_url"]
        self.timeout = cc.get("timeout_seconds", 30)
        self.retries = cc.get("retries", 3)
        self.delay = cc.get("delay_seconds", 0.6)
        self.priority = cfg.get("version_priority", ["release", "beta", "alpha"])
        self._mod_id_cache = {}

    def _get(self, url):
        headers = {"x-api-key": self.api_key}
        return http.get_json(
            self.client, url, headers=headers,
            retries=self.retries, delay=self.delay, timeout=self.timeout,
        )

    def resolve(self, cf_slug: str, loader: str, mc_version: str) -> ResolvedMod:
        """返回 :class:`ResolvedMod`，或抛 :class:`ResolveError`。"""
        if not self.api_key:
            raise ResolveError("curseforge_no_key", f"{cf_slug} 需要 CurseForge API key（.env）")

        mod_id = self._find_mod_id(cf_slug)
        if mod_id is None:
            raise ResolveError("not_found", f"CurseForge 未找到项目 {cf_slug}")

        files = self._list_files(mod_id, mc_version, loader)
        if not files:
            loader_files = self._list_files(mod_id, None, loader)
            if not loader_files:
                raise ResolveError("no_loader", f"{cf_slug} 无 {loader} 文件")
            raise ResolveError("no_game_version", f"{cf_slug} 无 {mc_version} 版本")

        chosen = pick_best(files, self.priority, key=lambda f: RELEASE_NAME.get(f.get("releaseType")))
        if chosen is None:
            raise ResolveError("no_acceptable_type", f"{cf_slug} 无 release/beta/alpha 文件")

        url = chosen.get("downloadUrl")
        if not url:
            raise ResolveError("download_failed", f"{cf_slug} 无下载地址")

        sha1 = next(
            (h.get("value") for h in chosen.get("hashes", []) if h.get("algo") == 1), None
        )
        filename = chosen.get("fileName") or f"{cf_slug}.jar"
        return ResolvedMod(filename=filename, url=url, sha1=sha1, meta=chosen)

    def _find_mod_id(self, slug: str):
        if slug in self._mod_id_cache:
            return self._mod_id_cache[slug]
        data = self._get(f"{self.base}/mods/search?gameId=432&slug={slug}")
        hits = data.get("data", [])
        if not hits:
            return None
        mod_id = hits[0]["id"]
        self._mod_id_cache[slug] = mod_id
        return mod_id

    def _list_files(self, mod_id, mc_version, loader):
        params = []
        if mc_version:
            params.append(f"gameVersion={mc_version}")
        if loader and loader != "any":
            params.append(f"modLoaderType={LOADER_TYPE.get(loader, 0)}")
        url = f"{self.base}/mods/{mod_id}/files"
        if params:
            url += "?" + "&".join(params)
        data = self._get(url)
        return data.get("data", [])
