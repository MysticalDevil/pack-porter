#!/usr/bin/env bash
# Minecraft 基础 Mod 安装器 - Unix 启动脚本
set -euo pipefail
cd "$(dirname "$0")"

if command -v uv >/dev/null 2>&1; then
    exec uv run mc-mod-installer "$@"
elif command -v python3 >/dev/null 2>&1; then
    export PYTHONPATH="$(pwd)/src${PYTHONPATH:+:$PYTHONPATH}"
    exec python3 -m mc_mod_installer "$@"
else
    echo "[错误] 未找到 uv 或 python3，请先安装 Python 3.10+ 与 uv（https://docs.astral.sh/uv/）。" >&2
    exit 1
fi
