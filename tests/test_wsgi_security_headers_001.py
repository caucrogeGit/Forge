"""Tests — WSGI-SECURITY-HEADERS-001 : socle de headers de sécurité WSGI.

Aligne le contrat de sécurité navigateur entre `python app.py` et le chemin
WSGI (`core.app.wsgi.create_wsgi_app`). Verrouille :

  * la présence des 5 headers de base (X-Frame-Options, X-Content-Type-Options,
    Referrer-Policy, Permissions-Policy, Content-Security-Policy) ;
  * le respect du `setdefault` — l'application qui définit explicitement un
    de ces headers garde la main ;
  * la décision HSTS : posé uniquement quand `wsgi.url_scheme == "https"`
    (cf docstring de `core/security/headers.py`) ;
  * l'absence de doublon Content-Type / Content-Length ;
  * que le statut HTTP, le body et le format WSGI ne sont pas altérés.

Aucune dépendance Jinja n'est requise : on stubbe le template_manager comme
`tests/test_wsgi_entrypoint_001.py`.
"""
from __future__ import annotations

from io import BytesIO

import pytest

from core.app.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from core.app.wsgi import _response_to_wsgi, create_wsgi_app

pytestmark = pytest.mark.usefixtures("_stub_renderer")


class _StubRenderer:
    def render(self, template: str, context: dict) -> str:
        return f"[{template}]"


@pytest.fixture
def _stub_renderer():
    previous = template_manager._renderer
    template_manager.register(_StubRenderer())
    try:
        yield
    finally:
        template_manager._renderer = previous


# ── Helpers ──────────────────────────────────────────────────────────────────


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None

    return start_response, captured


def _environ(*, scheme: str = "http", method: str = "GET", path: str = "/"):
    return {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(b""),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": scheme,
    }


def _headers_dict(headers_list: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Convertit la liste WSGI en dict insensible à la casse, valeurs en liste.

    Garde l'ordre d'insertion mais permet de détecter les doublons.
    """
    out: dict[str, list[str]] = {}
    for name, value in headers_list:
        out.setdefault(name.lower(), []).append(value)
    return out


def _build_app(*, with_override: dict | None = None):
    router = Router()

    def home(_request):
        return Response(200, "ok", content_type="text/plain; charset=utf-8",
                         headers=dict(with_override or {}))

    router.add("GET", "/", home, public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


@pytest.fixture
def wsgi_app():
    return create_wsgi_app(_build_app())


# ── Présence des 5 headers de base ──────────────────────────────────────────


class TestSecurityHeadersPresent:
    """Le socle de sécurité Forge est posé sur toute réponse WSGI nominale."""

    def test_x_frame_options_present_with_deny(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["x-frame-options"] == ["DENY"]

    def test_x_content_type_options_present(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["x-content-type-options"] == ["nosniff"]

    def test_referrer_policy_present(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["referrer-policy"] == ["strict-origin-when-cross-origin"]

    def test_permissions_policy_present(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        pp = h["permissions-policy"][0]
        for token in ("camera=()", "microphone=()", "geolocation=()", "payment=()"):
            assert token in pp, f"`{token}` absent de Permissions-Policy: {pp!r}"

    def test_content_security_policy_present(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        csp = h["content-security-policy"][0]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
        # Sans nonce en chemin WSGI : pas d'unsafe-inline, pas d'unsafe-eval.
        assert "unsafe-inline" not in csp
        assert "unsafe-eval" not in csp


# ── HSTS conditionné à HTTPS ────────────────────────────────────────────────


class TestHstsConditional:
    """HSTS est posé uniquement quand `wsgi.url_scheme == "https"`."""

    def test_hsts_absent_on_http(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(scheme="http"), start_response))
        h = _headers_dict(captured["headers"])
        assert "strict-transport-security" not in h, (
            "HSTS ne doit PAS être envoyé sur wsgi.url_scheme=http "
            "(derrière reverse proxy TLS-terminé, c'est le proxy qui le pose)."
        )

    def test_hsts_present_on_https(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(scheme="https"), start_response))
        h = _headers_dict(captured["headers"])
        assert "strict-transport-security" in h
        hsts = h["strict-transport-security"][0]
        assert "max-age=31536000" in hsts
        assert "includeSubDomains" in hsts


# ── Respect des overrides applicatifs (setdefault) ──────────────────────────


class TestApplicationOverrides:
    """Une application qui définit explicitement un header garde la main."""

    def test_csp_explicit_is_preserved(self):
        custom = "default-src 'none'; script-src 'self'"
        app = create_wsgi_app(_build_app(
            with_override={"Content-Security-Policy": custom},
        ))
        start_response, captured = _capture()
        list(app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["content-security-policy"] == [custom], (
            "La CSP explicite de l'application doit primer (setdefault)."
        )

    def test_referrer_policy_explicit_is_preserved(self):
        app = create_wsgi_app(_build_app(
            with_override={"Referrer-Policy": "no-referrer"},
        ))
        start_response, captured = _capture()
        list(app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["referrer-policy"] == ["no-referrer"]

    def test_x_frame_options_explicit_is_preserved(self):
        app = create_wsgi_app(_build_app(
            with_override={"X-Frame-Options": "SAMEORIGIN"},
        ))
        start_response, captured = _capture()
        list(app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["x-frame-options"] == ["SAMEORIGIN"]


# ── Pas de doublons sur Content-Type / Content-Length ───────────────────────


class TestNoDuplicateHeaders:
    """Les headers HTTP non bornés (Set-Cookie excepté) ne doivent pas doubler."""

    def test_content_type_not_duplicated(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert len(h.get("content-type", [])) == 1

    def test_content_length_not_duplicated(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert len(h.get("content-length", [])) == 1

    def test_x_frame_options_not_duplicated_when_overridden(self):
        app = create_wsgi_app(_build_app(
            with_override={"X-Frame-Options": "SAMEORIGIN"},
        ))
        start_response, captured = _capture()
        list(app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert len(h["x-frame-options"]) == 1


# ── Préservation du contrat existant (statut / body / Content-*) ────────────


class TestCoreContractPreserved:
    """Les invariants WSGI-ENTRYPOINT-001 / WSGI-APP-FACTORY-CONFIG-001
    ne sont pas cassés par l'ajout du socle de sécurité."""

    def test_status_preserved(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        assert captured["status"] == "200 OK"

    def test_body_preserved(self, wsgi_app):
        start_response, _ = _capture()
        body = b"".join(wsgi_app(_environ(), start_response))
        assert body == b"ok"

    def test_content_type_preserved(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["content-type"] == ["text/plain; charset=utf-8"]

    def test_content_length_matches_body(self, wsgi_app):
        start_response, captured = _capture()
        body = b"".join(wsgi_app(_environ(), start_response))
        h = _headers_dict(captured["headers"])
        assert h["content-length"] == [str(len(body))]

    def test_returns_iterable_of_bytes(self, wsgi_app):
        start_response, _ = _capture()
        chunks = list(wsgi_app(_environ(), start_response))
        for chunk in chunks:
            assert isinstance(chunk, bytes)


# ── Réponse 400 (mauvaise requête) ──────────────────────────────────────────


class TestBadRequestPath:
    """Le 400 d'entrée bénéficie aussi du socle de sécurité."""

    def test_bad_request_has_security_headers(self):
        """Force une requête invalide : PATH_INFO vide casse `Request` plus
        en aval ; on n'a pas de chemin facile pour la déclencher de l'extérieur.
        On valide à la place que `_response_to_wsgi` injecte les headers même
        sur une `Response(400, ...)` synthétique — c'est exactement ce que
        fait la branche d'erreur de `create_wsgi_app`."""
        start_response, captured = _capture()
        response = Response(400, b"Bad Request", "text/plain; charset=utf-8")
        list(_response_to_wsgi(response, start_response, is_https=False))
        h = _headers_dict(captured["headers"])
        # 5 headers de base présents (HSTS conditionné HTTPS, ici absent).
        assert "x-frame-options" in h
        assert "x-content-type-options" in h
        assert "referrer-policy" in h
        assert "permissions-policy" in h
        assert "content-security-policy" in h
        assert "strict-transport-security" not in h


# ── Source de vérité unique : helper directement testé ──────────────────────


class TestHelperContract:
    """Vérifie le contrat exact du helper centralisé."""

    def test_helper_uses_setdefault_for_x_frame_options(self):
        from core.security.headers import apply_security_headers

        headers = {"X-Frame-Options": "SAMEORIGIN"}
        apply_security_headers(headers, include_hsts=False)
        assert headers["X-Frame-Options"] == "SAMEORIGIN"

    def test_helper_sets_defaults_when_missing(self):
        from core.security.headers import apply_security_headers

        headers: dict[str, str] = {}
        apply_security_headers(headers, include_hsts=False)
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "Permissions-Policy" in headers

    def test_helper_hsts_only_when_requested(self):
        from core.security.headers import apply_security_headers

        without = {}
        apply_security_headers(without, include_hsts=False)
        assert "Strict-Transport-Security" not in without

        with_ = {}
        apply_security_headers(with_, include_hsts=True)
        assert with_["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"

    def test_helper_csp_only_when_provided(self):
        from core.security.headers import apply_security_headers

        without = {}
        apply_security_headers(without, include_hsts=False, csp=None)
        assert "Content-Security-Policy" not in without

        with_ = {}
        apply_security_headers(with_, include_hsts=False, csp="default-src 'self'")
        assert with_["Content-Security-Policy"] == "default-src 'self'"

    def test_helper_does_not_overwrite_csp_when_app_set_one(self):
        from core.security.headers import apply_security_headers

        headers = {"Content-Security-Policy": "default-src 'none'"}
        apply_security_headers(headers, include_hsts=False, csp="default-src 'self'")
        assert headers["Content-Security-Policy"] == "default-src 'none'"


# ── app.py partage la même source de vérité ─────────────────────────────────


class TestAppPyAndWsgiShareHelper:
    """Garde-fou méta : `app.py` et `core/app/wsgi.py` importent tous les deux
    `apply_security_headers` depuis `core.security.headers` — pas de
    duplication silencieuse de la liste de headers."""

    def test_app_py_imports_apply_security_headers(self):
        import pathlib
        source = pathlib.Path("app.py").read_text(encoding="utf-8")
        assert "from core.security.headers import apply_security_headers" in source

    def test_wsgi_imports_apply_security_headers(self):
        import pathlib
        source = pathlib.Path("core/app/wsgi.py").read_text(encoding="utf-8")
        assert "from core.security.headers import apply_security_headers" in source

    def test_app_py_no_longer_lists_security_headers_inline(self):
        """app.py ne doit plus poser les headers via send_header() en dur.

        On vérifie en particulier que les chaînes littérales (qui étaient
        embarquées dans `send_header`) ne réapparaissent pas en doublon —
        elles vivent désormais uniquement dans `core/security/headers.py`.
        """
        import pathlib
        source = pathlib.Path("app.py").read_text(encoding="utf-8")
        # send_header("X-Frame-Options", "DENY") -> remplacé par le helper
        assert 'send_header("X-Frame-Options"' not in source
        assert 'send_header("X-Content-Type-Options"' not in source
        assert 'send_header("Strict-Transport-Security"' not in source
        assert 'send_header("Referrer-Policy"' not in source
        assert 'send_header("Permissions-Policy"' not in source
