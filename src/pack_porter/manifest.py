"""加载 mods_manifest.json，按 loader 选组。"""

import json
from pathlib import Path


def load_manifest(path) -> dict:
    with open(Path(path), "r", encoding="utf-8") as f:
        return json.load(f)


def groups_for_loader(loader: str) -> list[str]:
    if loader == "fabric":
        return ["fabric", "common"]
    if loader == "forge":
        return ["forge", "common"]
    if loader == "neoforge":
        return ["neoforge", "common"]
    return ["common"]


def iter_mods(manifest_data: dict, loader: str):
    """按 loader 所属组迭代 mod 条目。"""
    groups = manifest_data.get("groups", {})
    for gkey in groups_for_loader(loader):
        group = groups.get(gkey) or {}
        for mod in group.get("mods", []):
            yield mod


def all_slugs(manifest_data: dict) -> set:
    slugs = set()
    for group in manifest_data.get("groups", {}).values():
        for mod in group.get("mods", []):
            if mod.get("slug"):
                slugs.add(mod["slug"])
    return slugs
