"""Tests — CORE-RESPONSE-MULTI-COOKIE-001 : plusieurs Set-Cookie par réponse.

`Response.headers` est un `dict[str, str]` : il ne porte qu'un seul Set-Cookie,
donc poser une session ET une préférence dans la même réponse en écrasait un.
`Response.add_cookie` accumule des cookies additionnels, chacun émis sur sa
propre ligne Set-Cookie par la couche serveur (WSGI, dev).
"""
from __future__ import annotations

from io import BytesIO

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.response import Response
from core.http.router import Router
from core.security.cookies import set_session_cookie


class TestAddCookie:
    def test_accumule_sans_ecraser(self):
        resp = Response(200, "ok")
        resp.add_cookie("pref=dark; Path=/")
        resp.add_cookie("lang=fr; Path=/")
        assert resp.set_cookies == ["pref=dark; Path=/", "lang=fr; Path=/"]

    def test_cookies_property_fusionne_session_et_additionnels(self):
        resp = Response(200, "ok")
        set_session_cookie(resp, "abc123")  # → headers["Set-Cookie"]
        resp.add_cookie("pref=dark; Path=/")  # → set_cookies
        names = resp.cookies
        assert "__Host-session_id" in names
        assert "pref" in names

    def test_session_seule_reste_dans_headers(self):
        # Compat : un seul cookie de session reste dans headers["Set-Cookie"]
        # (le helper de cookie et son test lisent cette clé).
        resp = Response(200, "ok")
        set_session_cookie(resp, "abc123")
        assert isinstance(resp.headers["Set-Cookie"], str)
        assert resp.set_cookies == []


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None

    return start_response, captured


def _environ(path="/"):
    return {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.url_scheme": "http",
    }


class TestWsgiEmission:
    def test_emet_plusieurs_lignes_set_cookie(self):
        def handler(request):
            resp = Response(200, "ok")
            set_session_cookie(resp, "abc123")
            resp.add_cookie("pref=dark; Path=/")
            resp.add_cookie("lang=fr; Path=/")
            return resp

        router = Router()
        router.add("GET", "/", handler, public=True, csrf=False)
        app = create_wsgi_app(Application(router, middlewares=[], api_routes_module=None))

        start_response, captured = _capture()
        list(app(_environ(), start_response))

        set_cookie_lines = [v for k, v in captured["headers"] if k == "Set-Cookie"]
        assert len(set_cookie_lines) == 3
        joined = " ".join(set_cookie_lines)
        assert "__Host-session_id=abc123" in joined
        assert "pref=dark" in joined
        assert "lang=fr" in joined
