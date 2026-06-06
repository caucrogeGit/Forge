"""Tests CORE-HTTP-FILE-RANGE-001 : service de fichiers en streaming + Range.

Trois niveaux :
  - parsing pur de l'en-tête ``Range`` (``core.http.byte_range``) ;
  - construction de ``Response.file`` (statuts, headers, tranches) ;
  - émission via la couche WSGI (corps itérable + Content-Length).
"""
from __future__ import annotations

import pytest

from core.http.byte_range import RangeSpec, parse_byte_range
from core.http.response import Response


# ---------------------------------------------------------------------------
# Parsing pur des plages
# ---------------------------------------------------------------------------

SIZE = 1000


@pytest.mark.parametrize("header,expected", [
    (None, None),
    ("", None),
    ("bytes=0-99", RangeSpec(True, 0, 99)),
    ("bytes=0-", RangeSpec(True, 0, 999)),
    ("bytes=500-", RangeSpec(True, 500, 999)),
    ("bytes=-100", RangeSpec(True, 900, 999)),
    ("bytes=990-5000", RangeSpec(True, 990, 999)),      # fin bornée à size-1
    ("  bytes=10-20  ", RangeSpec(True, 10, 20)),       # espaces tolérés
    ("bytes=1000-", RangeSpec(False, 0, 0)),            # start >= size
    ("bytes=2000-3000", RangeSpec(False, 0, 0)),        # hors limites
    ("bytes=500-200", RangeSpec(False, 0, 0)),          # start > end
    ("bytes=-0", RangeSpec(False, 0, 0)),               # suffixe nul
    ("bytes=0-1,5-9", None),                            # multi-plages → tout
    ("items=0-99", None),                               # mauvaise unité
    ("bytes=abc-def", None),                            # non numérique
    ("bytes=0", None),                                  # pas de tiret
])
def test_parse_byte_range(header, expected):
    assert parse_byte_range(header, SIZE) == expected


def test_parse_byte_range_empty_file():
    assert parse_byte_range("bytes=0-", 0) == RangeSpec(False, 0, 0)


# ---------------------------------------------------------------------------
# Response.file
# ---------------------------------------------------------------------------

class _FakeRequest:
    """Request minimal : expose juste ``header(name)``."""

    def __init__(self, headers: dict[str, str] | None = None):
        self._headers = headers or {}

    def header(self, name, default=None):
        return self._headers.get(name, default)


@pytest.fixture
def sample(tmp_path):
    data = bytes(range(256)) * 8  # 2048 octets déterministes
    path = tmp_path / "clip.bin"
    path.write_bytes(data)
    return path, data


def _drain(response: Response) -> bytes:
    return b"".join(response.stream)


def test_file_full_no_range(sample):
    path, data = sample
    resp = Response.file(path)
    assert resp.status == 200
    assert resp.content_length == len(data)
    assert resp.headers["Accept-Ranges"] == "bytes"
    assert "Content-Range" not in resp.headers
    assert _drain(resp) == data


def test_file_partial_range(sample):
    path, data = sample
    req = _FakeRequest({"Range": "bytes=0-9"})
    resp = Response.file(path, req)
    assert resp.status == 206
    assert resp.content_length == 10
    assert resp.headers["Content-Range"] == f"bytes 0-9/{len(data)}"
    assert _drain(resp) == data[0:10]


def test_file_suffix_range(sample):
    path, data = sample
    req = _FakeRequest({"Range": "bytes=-16"})
    resp = Response.file(path, req)
    assert resp.status == 206
    start = len(data) - 16
    assert resp.headers["Content-Range"] == f"bytes {start}-{len(data) - 1}/{len(data)}"
    assert _drain(resp) == data[-16:]


def test_file_open_ended_range(sample):
    path, data = sample
    req = _FakeRequest({"Range": "bytes=2000-"})
    resp = Response.file(path, req)
    assert resp.status == 206
    assert resp.content_length == len(data) - 2000
    assert _drain(resp) == data[2000:]


def test_file_unsatisfiable_range(sample):
    path, data = sample
    req = _FakeRequest({"Range": f"bytes={len(data)}-{len(data) + 100}"})
    resp = Response.file(path, req)
    assert resp.status == 416
    assert resp.headers["Content-Range"] == f"bytes */{len(data)}"
    assert resp.stream is None
    assert resp.body == b""


def test_file_content_type_override(sample):
    path, _ = sample
    resp = Response.file(path, content_type="video/mp4")
    assert resp.content_type == "video/mp4"


def test_file_content_type_default_non_none(sample):
    path, _ = sample
    resp = Response.file(path)
    assert resp.content_type  # jamais vide (octet-stream au pire)


def test_file_missing_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        Response.file(tmp_path / "absent.bin")


def test_ordinary_responses_have_no_stream():
    # Régression : text/html/json restent en body bytes, stream None.
    for resp in (Response.text("x"), Response.html("<p>x</p>"), Response.json({"a": 1})):
        assert resp.stream is None
        assert resp.content_length is None


# ---------------------------------------------------------------------------
# Émission WSGI
# ---------------------------------------------------------------------------

def test_wsgi_emits_stream_with_correct_content_length(sample):
    from core.app.wsgi import _response_to_wsgi

    path, data = sample
    req = _FakeRequest({"Range": "bytes=100-199"})
    resp = Response.file(path, req)

    captured: dict[str, object] = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body_iter = _response_to_wsgi(resp, start_response)

    assert captured["status"].startswith("206")
    assert captured["headers"]["Content-Length"] == "100"
    assert captured["headers"]["Accept-Ranges"] == "bytes"
    assert captured["headers"]["Content-Range"] == f"bytes 100-199/{len(data)}"
    assert b"".join(body_iter) == data[100:200]
