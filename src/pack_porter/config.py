"""配置加载（config.json + .env）与日志初始化。"""

import copy
import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

DEFAULTS = {
    "logging": {"level": "INFO", "console": True, "log_file": "logs/pack-porter.log"},
    "modrinth": {
        "base_url": "https://api.modrinth.com/v2",
        "user_agent": "pack-porter/0.1 (local use)",
        "timeout_seconds": 30,
        "retries": 4,
        "delay_seconds": 0.5,
    },
    "curseforge_api": {
        "base_url": "https://api.curseforge.com/v1",
        "timeout_seconds": 30,
        "retries": 4,
        "delay_seconds": 1.5,
    },
    "minecraft": {"search_up_levels": 2},
    "loader_rules": {"neoforge_min_version": "1.21"},
    "version_priority": ["release", "beta", "alpha"],
    "manifest_file": "mods_manifest.json",
}


def _deep_merge(base, extra):
    for key, value in extra.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def load_config(config_path=None, base_dir=None) -> dict:
    """加载 .env 与 config.json，返回合并后的配置 dict（含 ``_base_dir``）。"""
    base = Path(base_dir) if base_dir else Path.cwd()

    env_file = base / ".env"
    if env_file.exists():
        load_dotenv(env_file, interpolate=False)

    values = copy.deepcopy(DEFAULTS)
    cfg_file = Path(config_path) if config_path else (base / "config.json")
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                _deep_merge(values, json.load(f))
        except Exception as exc:  # noqa: BLE001
            print(f"[warn] 读取 config.json 失败，使用默认配置：{exc}")

    values["_base_dir"] = base
    return values


def curseforge_api_key() -> str:
    """从环境变量（由 .env 注入）读取 CurseForge API key。"""
    return os.getenv("CURSEFORGE_API_KEY", "").strip()


def setup_logging(cfg: dict, level_override=None):
    """按配置初始化根日志器。"""
    lc = cfg.get("logging", {})
    name = level_override or lc.get("level", "INFO")
    level = getattr(logging, str(name).upper(), logging.INFO)

    handlers = []
    if lc.get("console", True):
        handlers.append(logging.StreamHandler())
    log_file = lc.get("log_file")
    if log_file:
        p = Path(log_file)
        if not p.is_absolute():
            p = Path(cfg.get("_base_dir", Path.cwd())) / p
        p.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(p, encoding="utf-8"))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    for h in handlers:
        h.setFormatter(fmt)
        root.addHandler(h)
    return root
