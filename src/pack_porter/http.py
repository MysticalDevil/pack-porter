"""HTTP 封装（基于 httpx）：GET JSON 与流式下载。"""

import hashlib
import time

import httpx

from .errors import ResolveError


class NotFound(Exception):
    """资源不存在（HTTP 404），无需重试。"""


def new_client(timeout: float = 30.0) -> httpx.Client:
    """创建带重定向与合理超时的客户端；下载读超时放宽到至少 60s。"""
    read_timeout = max(timeout, 60.0)
    return httpx.Client(
        follow_redirects=True,
        timeout=httpx.Timeout(timeout, read=read_timeout),
    )


def get_json(client, url, headers=None, retries=3, delay=0.0, timeout=None):
    """GET 并解析 JSON。

    ``delay`` 既作为请求间节流（每次成功后休眠，避免限流），也作为重试退避基数。
    404 抛 :class:`NotFound`（不重试）；429 与网络错误按退避重试。
    """
    last = None
    for attempt in range(retries):
        try:
            resp = client.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 404:
                raise NotFound(url)
            if resp.status_code == 429:
                last = RuntimeError("HTTP 429 rate limited")
                time.sleep(max(delay, 1.0) * (attempt + 1))
                continue
            resp.raise_for_status()
            data = resp.json()
            if delay > 0:
                time.sleep(delay)  # 请求间节流
            return data
        except NotFound:
            raise
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries - 1 and delay > 0:
                time.sleep(delay * (attempt + 1))
    raise RuntimeError(f"GET {url} failed after {retries} tries: {last}")


def download(client, url, dest, headers=None, retries=3, timeout=None, expected_sha1=None) -> None:
    """流式下载到 ``dest``；可选校验 sha1（不匹配抛 :class:`ResolveError`）。"""
    last = None
    for attempt in range(retries):
        try:
            h = hashlib.sha1()
            with client.stream("GET", url, headers=headers, timeout=timeout) as resp:
                resp.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in resp.iter_bytes():
                        f.write(chunk)
                        h.update(chunk)
            if expected_sha1:
                actual = h.hexdigest()
                if actual.lower() != str(expected_sha1).lower():
                    raise ResolveError(
                        "hash_mismatch", f"sha1 校验失败：期望 {expected_sha1}，实际 {actual}"
                    )
            return
        except ResolveError:
            raise
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt < retries - 1:
                time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"download {url} failed after {retries} tries: {last}")
