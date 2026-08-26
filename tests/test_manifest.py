from pack_porter import manifest


def test_groups_for_loader():
    assert manifest.groups_for_loader("fabric") == ["fabric", "common"]
    assert manifest.groups_for_loader("forge") == ["forge_neoforge", "common"]
    assert manifest.groups_for_loader("neoforge") == ["forge_neoforge", "common"]
    assert manifest.groups_for_loader("unknown") == ["common"]
