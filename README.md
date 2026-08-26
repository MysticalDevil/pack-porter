# mc-mod-installer

Minecraft 基础 Mod 安装器：自动定位 `.minecraft`，按 `mods_manifest.json` 从
Modrinth（主）与 CurseForge（仅 `source=curseforge` 的 mod）下载 mod，并安装到
`versions/<实例>/mods/`。

## 环境要求

- [uv](https://docs.astral.sh/uv/)（管理 Python 3.14 环境与依赖）
- Python 3.10+（推荐 3.14）

## 快速开始

```bash
# 1) 安装依赖（首次）
uv sync

# 2) 配置 CurseForge API key（可选，仅安装 CurseForge 来源的 mod 时需要）
#    复制 .env.example 为 .env 并填入 key

# 3) 列出检测到的版本与 loader
uv run mc-mod-installer --list

# 4) 预演（只解析、不下载）
uv run mc-mod-installer --dry-run

# 5) 正式安装（交互式选择版本）
uv run mc-mod-installer
```

也可用包装脚本：

- Windows: `.\run.ps1 [args...]`
- Unix: `./run.sh [args...]`

## 参数

| 参数 | 说明 |
|---|---|
| `--minecraft-dir PATH` | 手动指定 `.minecraft` 目录 |
| `--list` | 仅列出检测到的版本/loader，不安装 |
| `--dry-run` | 解析但不下载 |
| `--version NAME` | 非交互，指定单个实例（可重复） |
| `--config PATH` | 指定 config.json |
| `--manifest PATH` | 指定 mods_manifest.json |
| `--log-level LEVEL` | 覆盖日志级别 |

## 配置

- `config.json`：日志、加载器规则、超时/重试等（不含密钥）。
- `.env`：`CURSEFORGE_API_KEY`（敏感，不入库）。
- `mods_manifest.json`：mod 清单（分组：fabric / common / forge / neoforge）。
