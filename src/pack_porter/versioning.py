"""版本号解析、比较与 loader 规则。"""

import re

_VERSION_RE = re.compile(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def parse_version_tuple(value) -> tuple:
    """``'1.21.1'`` -> ``(1, 21, 1)``；``'26.2'`` -> ``(26, 2, 0)``；非法返回 ``None``。"""
    if value is None:
        return None
    m = _VERSION_RE.match(str(value).strip())
    if not m:
        return None
    return tuple(int(x) if x is not None else 0 for x in m.groups())


def looks_like_version(value) -> bool:
    """是否形如版本号（以数字开头）。"""
    return bool(value) and str(value)[0].isdigit()


def loader_for_mc_version(mc_version, neoforge_min_version: str = "1.21") -> str:
    """按规则：MC >= 边界 -> neoforge，否则 -> forge（无法判断时保守返回 forge）。"""
    mc = parse_version_tuple(mc_version)
    boundary = parse_version_tuple(neoforge_min_version)
    if mc is None or boundary is None:
        return "forge"
    return "neoforge" if mc >= boundary else "forge"
