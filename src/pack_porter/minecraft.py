"""定位 .minecraft、枚举 versions、判定 MC 版本与 loader（启动器无关）。"""

import json
import re
import time
from pathlib import Path

from . import http
from .versioning import looks_like_version, loader_for_mc_version

MOJANG_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
_CACHE_DIR = Path.home() / ".cache" / "pack-porter"
_SHA1_LOOKUP_CAP = 40


def find_minecraft(start_dir, search_up_levels: int = 2) -> Path | None:
    """从 start_dir 向上 search_up_levels 层寻找 .minecraft（含 versions/）。"""
    start = Path(start_dir).resolve()
    for offset in range(search_up_levels + 1):
        d = start
        for _ in range(offset):
            d = d.parent
        if (d / "versions").is_dir():
            return d
        mc = d / ".minecraft"
        if (mc / "versions").is_dir():
            return mc
    return None


def list_versions(minecraft_dir) -> list[dict]:
    """枚举 versions/ 下的实例，返回 [{name, dir, json}, ...]。"""
    versions_dir = Path(minecraft_dir) / "versions"
    out = []
    for d in sorted(versions_dir.iterdir(), key=lambda p: p.name.lower()):
        if not d.is_dir():
            continue
        vj_path = _find_version_json(d)
        if vj_path is None:
            continue
        try:
            data = json.loads(vj_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        out.append({"name": d.name, "dir": d, "json": data})
    return out


def _find_version_json(d: Path) -> Path | None:
    p = d / (d.name + ".json")
    if p.is_file():
        return p
    for f in sorted(d.glob("*.json")):
        if f.name != "manifest.json":
            return f
    return None


_LOADER_ID_RE = re.compile(
    r"^(\d+(?:\.\d+)*)[-_](?:neoforge|forge|fabric|quilt|liteloader|rift|loader)",
    re.IGNORECASE,
)
_ASSET_INDEX_VER_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?$")


def detect_mc_version(vj: dict) -> str | None:
    """从标准版本 JSON 推断 MC 版本（离线部分）。"""
    inh = vj.get("inheritsFrom")
    if looks_like_version(inh):
        return inh

    vid = vj.get("id")
    if vid:
        # loader 版本名形如 "26.1.2-NeoForge_26.1.2.97" / "1.7.10-Forge10.13.4-1.7.10"
        m = _LOADER_ID_RE.match(str(vid))
        if m:
            return m.group(1)
        if looks_like_version(vid):
            return vid

    for lib in vj.get("libraries", []):
        name = lib.get("name", "")
        m = re.match(r"(?:net\.minecraft|com\.mojang):(?:client|minecraft):([0-9][^\s:]*)", name)
        if m:
            return m.group(1)

    # 老版本（≤1.7.10）：assetIndex.id 即 MC 版本，如 "1.7.10"
    aid = (vj.get("assetIndex") or {}).get("id")
    if aid and _ASSET_INDEX_VER_RE.match(str(aid)):
        return str(aid)

    return None


def detect_loader(vj: dict) -> str:
    """从 mainClass / libraries 判定 loader（启动器无关）。"""
    main_class = (vj.get("mainClass") or "").lower()
    libs = json.dumps(vj.get("libraries", []))
    if "fabricmc" in main_class or "fabric-loader" in libs:
        return "fabric"
    if "neoforged" in main_class or "neoforged" in libs:
        return "neoforge"
    if "modlauncher" in main_class or "launchwrapper" in main_class:
        return "forge"
    if "net.minecraftforge" in libs or "cpw.mods" in libs:
        return "forge"
    if main_class == "net.minecraft.client.main.main":
        return "vanilla"
    return "unknown"


def resolve_loader(raw_loader: str, mc_version: str | None, neoforge_min_version: str) -> str:
    """未知 loader 时按 MC 版本规则兜底。"""
    if raw_loader in ("fabric", "forge", "neoforge", "vanilla"):
        return raw_loader
    return loader_for_mc_version(mc_version, neoforge_min_version)


def resolve_mc_version_by_sha1(client, client_sha1: str) -> str | None:
    """用 client jar 的 sha1 反查 Mojang 版本（带磁盘缓存，每次最多抓 40 个版本 JSON）。"""
    if not client_sha1:
        return None
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = _CACHE_DIR / "sha1_to_version.json"

    sha1_cache = {}
    if cache_path.exists():
        try:
            sha1_cache = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            sha1_cache = {}
    if client_sha1 in sha1_cache:
        return sha1_cache[client_sha1]

    manifest = _load_manifest(client)
    versions = manifest.get("versions", [])
    releases = sorted(
        (v for v in versions if v.get("type") == "release"),
        key=lambda v: v.get("releaseTime", ""),
        reverse=True,
    )
    snapshots = sorted(
        (v for v in versions if v.get("type") == "snapshot"),
        key=lambda v: v.get("releaseTime", ""),
        reverse=True,
    )

    found = None
    fetched = 0
    for v in releases + snapshots:
        if fetched >= _SHA1_LOOKUP_CAP:
            break
        url = v.get("url")
        if not url:
            continue
        try:
            vj = http.get_json(client, url, headers={"User-Agent": "pack-porter/0.1"}, retries=1)
            fetched += 1
        except Exception:  # noqa: BLE001
            continue
        sha1 = (((vj.get("downloads") or {}).get("client") or {}) or {}).get("sha1")
        if sha1:
            sha1_cache[sha1] = v.get("id")
        if sha1 == client_sha1:
            found = v.get("id")
            break

    try:
        cache_path.write_text(json.dumps(sha1_cache, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return found


def _load_manifest(client) -> dict:
    path = _CACHE_DIR / "version_manifest.json"
    if path.exists() and (time.time() - path.stat().st_mtime) < 86400:
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            pass
    data = http.get_json(client, MOJANG_MANIFEST_URL, headers={"User-Agent": "pack-porter/0.1"})
    try:
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    return data
