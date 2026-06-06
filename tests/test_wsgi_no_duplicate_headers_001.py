"""Tests WSGI-NO-DUP-HEADERS-001 — pas de doublon Content-Type/Content-Length.

`_response_to_wsgi` calcule Content-Type et Content-Length en tête. Une route
qui pose un de ces en-têtes dans `response.headers` ne doit pas provoquer leur
émission en double (le calcul canonique garde la main, casse-insensible).
"""

from core.app.wsgi import _response_to_wsgi
from core.http.response import Response


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers

    return start_response, captured


def _values(headers, name):
    return [v for (k, v) in headers if k.lower() == name.lower()]


def test_no_duplicate_content_type_canonical_wins():
    resp = Response.text("ok")
    resp.headers["Content-Type"] = "application/json"  # tentative de doublon
    sr, cap = _capture()
    list(_response_to_wsgi(resp, sr))
    cts = _values(cap["headers"], "Content-Type")
    assert len(cts) == 1, f"un seul Content-Type attendu, vu {cts}"
    assert cts[0] == resp.content_type, "le Content-Type canonique doit gagner"


def test_no_duplicate_content_type_case_insensitive():
    resp = Response.text("ok")
    resp.headers["content-type"] = "application/json"  # casse différente
    sr, cap = _capture()
    list(_response_to_wsgi(resp, sr))
    assert len(_values(cap["headers"], "Content-Type")) == 1


def test_no_duplicate_content_length():
    resp = Response.text("hello")
    resp.headers["Content-Length"] = "999"
    sr, cap = _capture()
    list(_response_to_wsgi(resp, sr))
    cls = _values(cap["headers"], "Content-Length")
    assert len(cls) == 1, f"un seul Content-Length attendu, vu {cls}"


def test_custom_header_still_passes_through():
    resp = Response.text("ok")
    resp.headers["X-Custom"] = "yes"
    sr, cap = _capture()
    list(_response_to_wsgi(resp, sr))
    assert _values(cap["headers"], "X-Custom") == ["yes"]
