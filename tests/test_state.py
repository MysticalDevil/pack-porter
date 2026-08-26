from pack_porter.state import StateStore


def test_record_and_old_files(tmp_path):
    s = StateStore(tmp_path)
    assert s.old_files("lithium") == []
    s.record("lithium", "lithium-1.jar")
    assert s.old_files("lithium") == ["lithium-1.jar"]
    s.record("lithium", "lithium-2.jar")
    assert s.old_files("lithium") == ["lithium-2.jar"]


def test_persist(tmp_path):
    s = StateStore(tmp_path)
    s.record("a", "a.jar")
    s2 = StateStore(tmp_path)
    assert s2.old_files("a") == ["a.jar"]


def test_corrupt_state_resets(tmp_path):
    p = tmp_path / ".pack-porter-installed.json"
    p.write_text("not json", encoding="utf-8")
    s = StateStore(tmp_path)
    assert s.old_files("a") == []
