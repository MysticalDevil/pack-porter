from pack_porter import versioning


def test_parse_version_tuple():
    assert versioning.parse_version_tuple("1.21.1") == (1, 21, 1)
    assert versioning.parse_version_tuple("26.2") == (26, 2, 0)
    assert versioning.parse_version_tuple("1.7.10") == (1, 7, 10)
    assert versioning.parse_version_tuple("26.3-snapshot-8") == (26, 3, 0)
    assert versioning.parse_version_tuple("abc") is None
    assert versioning.parse_version_tuple(None) is None


def test_looks_like_version():
    assert versioning.looks_like_version("1.21") is True
    assert versioning.looks_like_version("26.2") is True
    assert versioning.looks_like_version("Latest Vanilla") is False
    assert versioning.looks_like_version("") is False
    assert versioning.looks_like_version(None) is False


def test_loader_for_mc_version():
    assert versioning.loader_for_mc_version("1.20.4") == "forge"
    assert versioning.loader_for_mc_version("1.21") == "neoforge"
    assert versioning.loader_for_mc_version("26.2") == "neoforge"
    assert versioning.loader_for_mc_version("1.7.10") == "forge"
    assert versioning.loader_for_mc_version(None) == "forge"


def test_pick_best():
    items = [
        {"version_type": "beta"},
        {"version_type": "release"},
        {"version_type": "alpha"},
    ]
    key = lambda v: v["version_type"]  # noqa: E731
    assert versioning.pick_best(items, ["release", "beta", "alpha"], key) == items[1]
    assert versioning.pick_best([{"version_type": "beta"}], ["release", "beta", "alpha"], key)["version_type"] == "beta"
    assert versioning.pick_best([], ["release"], key) is None
    assert versioning.pick_best([{"version_type": "unknown"}], ["release"], key) is None
