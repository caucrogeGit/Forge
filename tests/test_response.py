from core.http.response import Response


class TestResponse:
    def test_status(self):
        assert Response(200, "").status == 200

    def test_body_str_converti_en_bytes(self):
        assert Response(200, "hello").body == b"hello"

    def test_body_bytes_inchange(self):
        assert Response(200, b"hello").body == b"hello"

    def test_body_none_donne_bytes_vides(self):
        assert Response(200, None).body == b""

    def test_headers(self):
        r = Response(302, headers={"Location": "/x"})
        assert r.headers["Location"] == "/x"

    def test_content_type_par_defaut(self):
        assert "text/html" in Response(200, "").content_type

    def test_body_encode_utf8(self):
        assert Response(200, "éàü").body == "éàü".encode("utf-8")
