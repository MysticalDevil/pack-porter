import hashlib

from pack_porter import http
from pack_porter.errors import ResolveError


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


def test_sha1_match(tmp_path):
    data = b"hello world"
    dest = tmp_path / "x.jar"
    http.download(FakeClient([data]), "https://x", dest, expected_sha1=hashlib.sha1(data).hexdigest())
    assert dest.read_bytes() == data


def test_sha1_mismatch(tmp_path):
    data = b"hello world"
    dest = tmp_path / "x.jar"
    try:
        http.download(FakeClient([data]), "https://x", dest, expected_sha1="0" * 40)
    except ResolveError as exc:
        assert exc.reason == "hash_mismatch"
    else:
        raise AssertionError("should raise hash_mismatch")
