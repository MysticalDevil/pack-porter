"""命令行入口与主流程编排。"""

import argparse
import logging
import unicodedata
from collections import Counter
from pathlib import Path

from rich.console import Console

from . import config as config_mod
from . import http, installer, manifest, minecraft
from .curseforge import CurseForgeClient
from .errors import ResolveError
from .modrinth import ModrinthClient

log = logging.getLogger(__name__)
console = Console()

_STATUS_LABELS = {
    "ok": "成功",
    "skipped_exists": "已存在跳过",
    "not_found": "未找到",
    "no_game_version": "无该 MC 版本",
    "no_loader": "无该 loader",
    "no_acceptable_type": "无 release/beta/alpha",
    "download_failed": "下载失败",
    "curseforge_no_key": "缺 CurseForge key",
    "vanilla": "原版跳过",
}


def _display_width(s) -> int:
    """终端显示宽度：CJK（W/F）计 2，其余计 1。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in str(s))


def _pad(s, width: int, align: str = "left") -> str:
    gap = width - _display_width(s)
    if gap <= 0:
        return str(s)
    return (str(s) + " " * gap) if align == "left" else (" " * gap + str(s))


def _print_table(title, headers, rows, aligns=None):
    """CJK 感知对齐的简单表格。"""
    aligns = aligns or ["left"] * len(headers)
    widths = [_display_width(h) for h in headers]
    for r in rows:
        for i, c in enumerate(r):
            widths[i] = max(widths[i], _display_width(c))

    def _cells(cells):
        return "│ " + " │ ".join(_pad(c, w, a) for c, w, a in zip(cells, widths, aligns)) + " │"

    def _border(left, mid, right):
        return left + mid.join("─" * (w + 2) for w in widths) + right

    if title:
        total = sum(widths) + 3 * len(widths) + 1
        left = max((total - _display_width(title)) // 2, 0)
        console.print(" " * left + title)
    console.print(_border("┌", "┬", "┐"))
    console.print(_cells(headers))
    console.print(_border("├", "┼", "┤"))
    for r in rows:
        console.print(_cells(r))
    console.print(_border("└", "┴", "┘"))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Minecraft 基础 Mod 安装器（Modrinth + CurseForge）")
    p.add_argument("--minecraft-dir", help="手动指定 .minecraft 目录")
    p.add_argument("--config", help="config.json 路径")
    p.add_argument("--manifest", help="mods_manifest.json 路径")
    p.add_argument("--list", action="store_true", help="仅列出检测到的版本/loader，不安装")
    p.add_argument("--dry-run", action="store_true", help="解析版本但不下载")
    p.add_argument("--version", action="append", default=[], help="指定实例名（可重复，非交互）")
    p.add_argument("--log-level", help="覆盖日志级别（DEBUG/INFO/WARNING/ERROR）")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    base_dir = Path.cwd()

    cfg = config_mod.load_config(args.config, base_dir=base_dir)
    config_mod.setup_logging(cfg, args.log_level)

    client = http.new_client(cfg["modrinth"].get("timeout_seconds", 30))

    # 1) 定位 .minecraft
    if args.minecraft_dir:
        mc_dir = Path(args.minecraft_dir)
    else:
        mc_dir = minecraft.find_minecraft(base_dir, cfg["minecraft"].get("search_up_levels", 2))
    if mc_dir is None:
        console.print("[red]未找到 .minecraft（含 versions/）。可用 --minecraft-dir 指定。[/red]")
        return 1
    log.info(".minecraft = %s", mc_dir)

    # 2) 枚举 + 判型
    versions = minecraft.list_versions(mc_dir)
    if not versions:
        console.print("[red]versions/ 下没有可识别的实例。[/red]")
        return 1
    detected = _detect_all(versions, client, cfg)

    if args.list:
        _print_detected(detected)
        return 0

    # 3) 选择实例
    selected = _select(detected, args.version)
    if not selected:
        console.print("[yellow]未选择任何实例。[/yellow]")
        return 0

    # 4) 加载清单
    manifest_path = args.manifest or (
        Path(cfg.get("_base_dir", base_dir)) / cfg.get("manifest_file", "mods_manifest.json")
    )
    try:
        manifest_data = manifest.load_manifest(manifest_path)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]读取清单失败：{exc}[/red]")
        return 1

    mr = ModrinthClient(client, cfg)
    cf = CurseForgeClient(client, cfg, config_mod.curseforge_api_key())
    inst = installer.Installer(client, cfg)

    # 5) 逐个实例安装
    results = []
    for sel in selected:
        results.extend(_process_instance(sel, manifest_data, mr, cf, inst, args.dry_run))

    _print_summary(results)
    return 0


def _detect_all(versions, client, cfg) -> list[dict]:
    rule = cfg["loader_rules"]["neoforge_min_version"]
    detected = []
    for v in versions:
        vj = v["json"]
        mc_ver = minecraft.detect_mc_version(vj)
        if mc_ver is None:
            sha1 = (((vj.get("downloads") or {}).get("client") or {}) or {}).get("sha1")
            mc_ver = minecraft.resolve_mc_version_by_sha1(client, sha1)
        raw = minecraft.detect_loader(vj)
        loader = minecraft.resolve_loader(raw, mc_ver, rule)
        detected.append({"name": v["name"], "dir": v["dir"], "mc_version": mc_ver, "loader": loader})
    return detected


def _print_detected(detected):
    rows = [[str(i), v["name"], v["mc_version"] or "?", v["loader"]] for i, v in enumerate(detected, 1)]
    _print_table("检测到的版本", ["#", "实例", "MC 版本", "loader"], rows, aligns=["right", "left", "left", "left"])


def _select(detected, version_names):
    if version_names:
        out = []
        for name in version_names:
            match = next((v for v in detected if v["name"] == name), None)
            if match:
                out.append(match)
            else:
                console.print(f"[red]未找到实例：{name}[/red]")
        return out

    _print_detected(detected)
    raw = console.input("[green]输入要安装的实例序号（空格分隔，all=全部，回车跳过）：[/green]").strip()
    if not raw:
        return []
    if raw.lower() in ("all", "a"):
        return detected
    idx = []
    for tok in raw.split():
        try:
            idx.append(int(tok) - 1)
        except ValueError:
            pass
    return [detected[i] for i in idx if 0 <= i < len(detected)]


def _process_instance(sel, manifest_data, mr, cf, inst, dry_run) -> list[dict]:
    loader = sel["loader"]
    mc_ver = sel["mc_version"]
    if loader == "vanilla":
        console.print(f"[yellow]跳过原版实例 {sel['name']}[/yellow]")
        return [{"name": sel["name"], "status": "vanilla", "detail": "原版实例", "filename": None}]
    if mc_ver is None:
        console.print(f"[yellow]实例 {sel['name']} 无法确定 MC 版本，跳过[/yellow]")
        return [{"name": sel["name"], "status": "no_game_version", "detail": "无法确定 MC 版本", "filename": None}]

    mods = list(manifest.iter_mods(manifest_data, loader))
    console.print(f"\n[bold]== {sel['name']}（{mc_ver} / {loader}）：{len(mods)} 个 mod ==[/bold]")

    manifest_slugs = manifest.all_slugs(manifest_data)
    dep_cache = {}
    required_missing = {}
    results = []

    for i, mod in enumerate(mods, 1):
        name = mod.get("name") or mod.get("slug") or mod.get("curseforge") or "?"
        try:
            if mod.get("source") == "curseforge":
                filename, url, meta = cf.resolve(mod["curseforge"], loader, mc_ver)
            else:
                filename, url, meta = mr.resolve(mod["slug"], loader, mc_ver)
                for pid in mr.required_deps(meta):
                    slug = _resolve_project_slug(mr, pid, dep_cache)
                    if slug and slug not in manifest_slugs:
                        required_missing.setdefault(name, []).append(slug)

            status = inst.install(sel["dir"], filename, url, dry_run=dry_run, headers={"User-Agent": "mc-mod-installer/0.1"})
            results.append({"name": name, "status": status, "detail": "", "filename": filename})
            if status == "ok":
                console.print(f"  [green]✓[/green] ({i}/{len(mods)}) {name} -> {filename}")
            else:
                console.print(f"  [yellow]·[/yellow] ({i}/{len(mods)}) {name} 已存在，跳过")
        except ResolveError as exc:
            results.append({"name": name, "status": exc.reason, "detail": exc.message, "filename": None})
            console.print(f"  [red]✗[/red] ({i}/{len(mods)}) {name}: {exc.message}")
        except Exception as exc:  # noqa: BLE001  网络/未知错误：只记失败，不中断整个流程
            results.append({"name": name, "status": "download_failed", "detail": str(exc), "filename": None})
            console.print(f"  [red]✗[/red] ({i}/{len(mods)}) {name}: {exc}")

    if required_missing:
        console.print("[yellow]提示：以下 mod 声明了清单外的必需依赖（本工具未自动下载）：[/yellow]")
        for mod_name, deps in required_missing.items():
            console.print(f"  - {mod_name}: {', '.join(deps)}")

    return results


def _resolve_project_slug(mr, project_id, cache):
    if project_id in cache:
        return cache[project_id]
    proj = mr.get_project(project_id)
    slug = (proj or {}).get("slug")
    cache[project_id] = slug
    return slug


def _print_summary(results):
    if not results:
        return
    counts = Counter(r["status"] for r in results)
    rows = [[_STATUS_LABELS.get(s, s), str(n)] for s, n in sorted(counts.items())]
    _print_table("安装汇总", ["状态", "数量"], rows, aligns=["left", "right"])

    failed = [r for r in results if r["status"] not in ("ok", "skipped_exists")]
    if failed:
        console.print("\n[bold yellow]以下 mod 未安装成功：[/bold yellow]")
        for r in failed:
            label = _STATUS_LABELS.get(r["status"], r["status"])
            console.print(f"  - {r['name']}: {label} {r['detail']}".rstrip())
    else:
        console.print("\n[green]全部安装完成。[/green]")
