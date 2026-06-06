"""Tests URL-FOR-ENCODING-001 — url_for encode les paramètres de chemin.

Sans encodage, un paramètre contenant /, espace, ?, # ou & produisait une URL
malformée (voire un vecteur d'injection de segment). url_for encode désormais
chaque valeur substituée.
"""

from core.http.router import Router


def _h(request):
    return None


def _router():
    r = Router()
    r.add("GET", "/clients/{id}", _h, name="client_show")
    r.add("GET", "/files/{slug}", _h, name="file_show")
    return r


def test_plain_value_unchanged():
    assert _router().url_for("client_show", id=42) == "/clients/42"


def test_space_is_encoded():
    assert _router().url_for("file_show", slug="my file") == "/files/my%20file"


def test_slash_in_value_is_encoded():
    # safe='' : un paramètre ne doit pas traverser de segment de chemin.
    assert _router().url_for("file_show", slug="a/b") == "/files/a%2Fb"


def test_query_and_fragment_chars_encoded():
    url = _router().url_for("file_show", slug="x?y#z&w")
    assert "?" not in url and "#" not in url and "&" not in url
    assert url == "/files/x%3Fy%23z%26w"
