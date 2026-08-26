from pack_porter import minecraft


def test_detect_mc_version_from_id():
    assert minecraft.detect_mc_version({"id": "26.3-snapshot-8"}) == "26.3-snapshot-8"
    assert minecraft.detect_mc_version({"id": "1.21.1"}) == "1.21.1"


def test_detect_mc_version_from_inherits_from():
    vj = {"inheritsFrom": "1.21.1", "id": "fabric-loader-0.16.9-1.21.1"}
    assert minecraft.detect_mc_version(vj) == "1.21.1"


def test_detect_mc_version_strips_loader_suffix():
    assert minecraft.detect_mc_version({"id": "26.1.2-NeoForge_26.1.2.97"}) == "26.1.2"
    assert minecraft.detect_mc_version({"id": "1.7.10-Forge10.13.4.1614-1.7.10"}) == "1.7.10"


def test_detect_mc_version_from_libraries():
    vj = {"id": "GT New Horizons", "libraries": [{"name": "net.minecraft:client:1.7.10"}]}
    assert minecraft.detect_mc_version(vj) == "1.7.10"


def test_detect_mc_version_from_asset_index():
    vj = {"id": "GT New Horizons", "assetIndex": {"id": "1.7.10"}}
    assert minecraft.detect_mc_version(vj) == "1.7.10"


def test_detect_mc_version_none():
    assert minecraft.detect_mc_version({"id": "Latest Vanilla"}) is None


def test_detect_loader_fabric():
    assert minecraft.detect_loader({"mainClass": "net.fabricmc.loader.impl.launch.knot.KnotClient"}) == "fabric"
    assert minecraft.detect_loader({"libraries": [{"name": "net.fabricmc:fabric-loader:0.19.3"}]}) == "fabric"


def test_detect_loader_modded():
    assert minecraft.detect_loader({"mainClass": "net.neoforged.fml.startup.Client"}) == "modded"
    assert minecraft.detect_loader({"mainClass": "cpw.mods.modlauncher.Launcher"}) == "modded"
    assert minecraft.detect_loader({"libraries": [{"name": "net.minecraftforge:forge:1.7.10"}]}) == "modded"


def test_detect_loader_vanilla():
    assert minecraft.detect_loader({"mainClass": "net.minecraft.client.main.Main"}) == "vanilla"


def test_detect_loader_unknown():
    assert minecraft.detect_loader({"mainClass": "some.unknown.Main"}) == "unknown"


def test_resolve_loader():
    assert minecraft.resolve_loader("fabric", "1.19.4", "1.21") == "fabric"
    assert minecraft.resolve_loader("vanilla", "1.19.4", "1.21") == "vanilla"
    assert minecraft.resolve_loader("modded", "1.18.2", "1.21") == "forge"
    assert minecraft.resolve_loader("modded", "26.1.2", "1.21") == "neoforge"
    assert minecraft.resolve_loader("unknown", "1.7.10", "1.21") == "forge"
