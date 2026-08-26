from pack_porter import installer
from pack_porter.model import ResolvedMod
from pack_porter.state import StateStore


class FakeStreamResponse:
    def __init__(self, chunks):
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        pass

    def iter_bytes(self):
        yield from self._chunks


class FakeClient:
    def __init__(self, chunks):
        self.chunks = chunks

    def stream(self, *a, **k):
        return FakeStreamResponse(self.chunks)


def _make_installer(client):
    return installer.Installer(
        client,
        {"modrinth": {"timeout_seconds": 5, "retries": 1}, "cleanup_old_versions": True, "verify_sha1": False},
    )


def test_cleanup_old_version(tmp_path):
    mods_dir = tmp_path / "mods"
    mods_dir.mkdir()
    old = mods_dir / "lithium-old.jar"
    old.write_bytes(b"old")
    StateStore(tmp_path).record("lithium", "lithium-old.jar")

    inst = _make_installer(FakeClient([b"newdata"]))
    resolved = ResolvedMod(filename="lithium-new.jar", url="https://x", sha1=None, meta={})
    status = inst.install(tmp_path, "lithium", resolved, headers={})

    assert status == "ok"
    assert not old.exists()
    assert (mods_dir / "lithium-new.jar").exists()
    assert StateStore(tmp_path).old_files("lithium") == ["lithium-new.jar"]
