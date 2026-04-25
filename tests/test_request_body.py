"""
Tests de core/http/request.py — gestion du Content-Length et RequestEntityTooLarge.
"""
import io
from types import SimpleNamespace

import pytest

from core.http.request import Request, RequestEntityTooLarge, MAX_BODY_SIZE


class _FakeHeaders:
    def __init__(self, data: dict):
        self._data = {k.lower(): v for k, v in data.items()}

    def get(self, name, default=""):
        return self._data.get(name.lower(), default)


def _handler(method="POST", path="/", headers=None, body=b""):
    h = headers or {}
    return SimpleNamespace(
        command=method,
        path=path,
        headers=_FakeHeaders(h),
        rfile=io.BytesIO(body),
        client_address=("127.0.0.1", 12345),
    )


class TestContentLength:
    def test_body_normal_parse(self):
        body = b"nom=Alice&age=30"
        req = Request(_handler(body=body, headers={"Content-Length": str(len(body))}))
        assert req.body.get("nom") == ["Alice"]
        assert req.body.get("age") == ["30"]

    def test_content_length_exactement_max_accepte(self):
        body = b"x=" + b"a" * (MAX_BODY_SIZE - 2)
        req = Request(_handler(body=body, headers={"Content-Length": str(MAX_BODY_SIZE)}))
        assert req.body is not None

    def test_content_length_depasse_leve_exception(self):
        with pytest.raises(RequestEntityTooLarge):
            Request(_handler(headers={"Content-Length": str(MAX_BODY_SIZE + 1)}))

    def test_content_length_tres_grand_leve_exception(self):
        with pytest.raises(RequestEntityTooLarge):
            Request(_handler(headers={"Content-Length": "104857600"}))  # 100 Mo

    def test_content_length_negatif_traite_comme_zero(self):
        req = Request(_handler(headers={"Content-Length": "-1"}))
        assert req.body == {}

    def test_content_length_invalide_traite_comme_zero(self):
        req = Request(_handler(headers={"Content-Length": "abc"}))
        assert req.body == {}

    def test_content_length_absent_traite_comme_zero(self):
        req = Request(_handler())
        assert req.body == {}

    def test_get_sans_body_ignore_content_length(self):
        req = Request(_handler(method="GET", path="/", headers={"Content-Length": "999999999"}))
        assert req.body == {}

    def test_multipart_parse_body_et_files(self):
        boundary = "----ForgeBoundary"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="titre"\r\n\r\n'
            "Avatar\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="avatar"; filename="avatar.png"\r\n'
            "Content-Type: image/png\r\n\r\n"
        ).encode("utf-8") + b"PNGDATA" + f"\r\n--{boundary}--\r\n".encode("utf-8")

        req = Request(_handler(
            body=body,
            headers={
                "Content-Length": str(len(body)),
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
        ))

        assert req.body == {"titre": ["Avatar"]}
        assert req.files["avatar"].filename == "avatar.png"
        assert req.files["avatar"].content_type == "image/png"
        assert req.files["avatar"].read() == b"PNGDATA"
