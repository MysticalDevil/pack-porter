# Pack Porter

> Minecraft 基础 Mod 安装器：自动定位 `.minecraft`，按 `mods_manifest.json` 从 **Modrinth**（主）与 **CurseForge**（部分）下载 mod，安装到 `versions/<实例>/mods/`。

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
uv run pack-porter --list

# 4) 预演（只解析、不下载）
uv run pack-porter --dry-run

# 5) 正式安装（交互式选择版本）
uv run pack-porter
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

## 默认 Mod 列表

> 分组语义：`Fabric 专属` 仅对 Fabric 实例安装；`通用` 对 Fabric/Forge/NeoForge 均尝试（按目标加载器自动筛版本）；`Forge/NeoForge 专属` 对 Forge/NeoForge 实例安装，loader 按 MC 版本自动判断（`<1.21` Forge，`>=1.21` NeoForge）。
> 源头列 = Modrinth slug（默认）或 CurseForge slug（标注 `CurseForge`）。

### Fabric 专属（17）

| 中文名 | 英文名 | 源头 |
|---|---|---|
| Fabric API | Fabric API | `fabric-api` |
| 配置界面 | Configured | `configured`（CurseForge） |
| 地毯 | Carpet | `carpet` |
| 语言重载 | Language Reload | `language-reload` |
| 文本占位符 API | Text Placeholder API | `placeholder-api` |
| 模组菜单 | Mod Menu | `modmenu` |
| Fabric 语言 Kotlin | Fabric Language Kotlin | `fabric-language-kotlin` |
| 物品栏整理 | Inventory Sorting | `inventory-sorting` |
| 连续性（连接纹理） | Continuity | `continuity` |
| REI 物品管理器 | Roughly Enough Items (REI) | `rei` |
| 连锁采集 | VeinMiner | `veinminer` |
| 连锁采集快捷键 | VeinMiner Hotkey | `veinminer-client` |
| MaLiLib | MaLiLib | `malilib` |
| 投影 | Litematica | `litematica` |
| Tweakeroo | Tweakeroo | `tweakeroo` |
| 物品滚轮 | Item Scroller | `item-scroller` |
| 迷你 HUD | MiniHUD | `minihud` |

### 通用（33）

| 中文名 | 英文名 | 源头 |
|---|---|---|
| Iris 光影 | Iris Shaders | `iris` |
| 实体渲染机制优化 | Entity Culling | `entityculling` |
| 铁氧体磁芯 | FerriteCore | `ferrite-core` |
| 锂 | Lithium | `lithium` |
| 实体纹理特性 | Entity Texture Features (ETF) | `entitytexturefeatures` |
| 钠·扩展 | Sodium Extra | `sodium-extra` |
| 苹果皮 | AppleSkin | `appleskin` |
| 搜索栏 | Searchables | `searchables` |
| 键位冲突显示 | Controlling | `controlling` |
| Reese 的钠视频界面 | Reese's Sodium Options | `reeses-sodium-options` |
| 经验机制改革 | Clumps | `clumps` |
| Prickle | Prickle | `prickle` |
| 玉 | Jade | `jade` |
| Xaero 的小地图 | Xaero's Minimap | `xaeros-minimap` |
| 实体模型特性 | Entity Model Features (EMF) | `entity-model-features` |
| 搬运 | Carry On | `carry-on` |
| 更好的 F3 | BetterF3 | `betterf3` |
| 聊天头像 | Chat Heads | `chat-heads` |
| 动态 FPS | Dynamic FPS | `dynamic-fps` |
| Cloth 配置 API | Cloth Config API | `cloth-config` |
| 立即优化 | ImmediatelyFast | `immediatelyfast` |
| 附魔描述 | Enchantment Descriptions | `enchantment-descriptions` |
| Xaero 的世界地图 | Xaero's World Map | `xaeros-world-map` |
| Architectury API | Architectury API | `architectury-api` |
| Lambd 的动态光源 | LambDynamicLights | `lambdynamiclights` |
| 更多动画 | Not Enough Animations | `not-enough-animations` |
| 存档置顶 | Cherished Worlds | `cherished-worlds` |
| 钠·土径阴影 | Sodium Shadowy Path Blocks (SSPB) | `sodium-shadowy-path-blocks` |
| TCD Commons API | TCDCommons API | `tcdcommons` |
| 更好的统计信息界面 | Better Statistics Screen | `better-stats` |
| Forge 配置 API 移植 | Forge Config API Port | `forge-config-api-port` |
| 钠 | Sodium | `sodium` |
| 3D 皮肤层 | 3D Skin Layers | `3dskinlayers` |

### Forge/NeoForge 专属（5）

> loader 按 MC 版本自动判断：`< 1.21` → Forge，`>= 1.21` → NeoForge。

| 中文名 | 英文名 | 源头 |
|---|---|---|
| JEI 物品管理器 | Just Enough Items (JEI) | `jei` |
| FTB 连锁破坏 | FTB Ultimine | `ftb-ultimine-forge`（CurseForge） |
| 连接纹理 | Fusion (Connected Textures) | `fusion-connected-textures` |
| 鼠标手势 | Mouse Tweaks | `mouse-tweaks` |
| 物品栏整理 | Inventory Sorter | `inventory-sorter`（CurseForge） |

## 说明

- 已排除：旅行者背包（Traveler's Backpack）。
- 加载器规则：MC `< 1.21` 使用 Forge/Fabric；MC `>= 1.21` 使用 NeoForge/Fabric。
- 依赖：v1 仅警告不自动下载必需依赖。
- 终端表格若中文对不齐，请使用等宽 CJK 字体（如 Sarasa Mono / Cascadia Code）。
