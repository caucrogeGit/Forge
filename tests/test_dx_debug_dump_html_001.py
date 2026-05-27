"""Tests — DX-DEBUG-DUMP-HTML-001.

Verrouille le contrat du rendu HTML pédagogique de
``Response.debug(obj)`` en mode développement :

- Content-Type ``text/html; charset=utf-8`` en `APP_ENV=dev` ;
- titre « Debug Forge » et type de l'objet affichés ;
- rendu récursif pour ``dict``/``list``/``tuple``/``set`` ;
- déballage de ``.data`` si exploitable ;
- masquage des champs sensibles (Authorization, Cookie, password,
  token, csrf, api_key, secret, …) ;
- échappement HTML systématique des chaînes ;
- bornage de profondeur (``MAX_DEPTH``) ;
- détection des références circulaires ;
- comportement sécurisé inchangé en `APP_ENV=prod` ;
- ``Response.text``/`.html`/`.json` ne régressent pas.

Aucun handler HTTP n'est instancié — un mini-handler ``SimpleNamespace``
suffit pour construire un `Request` réel.
"""

from __future__ import annotations

import io
import json as _json
from types import SimpleNamespace

import pytest

from core import forge as forge_module
from core.http.debug_dumper import (
    CYCLE_MARKER,
    MAX_DEPTH,
    MAX_DEPTH_MARKER,
    render_debug_html,
)
from core.http.request import MASKED_VALUE, Request
from core.http.response import Response


# ── Mini handler (mêmes briques que la suite API-INSPECTABLE-…) ─────────────


class _FakeHeaders:
    def __init__(self, data: dict[str, str]):
        self._data = dict(data)
        self._lower = {k.lower(): k for k in self._data}

    def get(self, name, default=None):
        if name in self._data:
            return self._data[name]
        original_key = self._lower.get(name.lower())
        if original_key is None:
            return default
        return self._data[original_key]

    def keys(self):
        return list(self._data.keys())

    def items(self):
        return list(self._data.items())


def _handler(method="GET", path="/", headers=None, body=b""):
    return SimpleNamespace(
        command=method,
        path=path,
        headers=_FakeHeaders(headers or {}),
        rfile=io.BytesIO(body),
        client_address=("127.0.0.1", 12345),
    )


# ── Fixture environnement APP_ENV ───────────────────────────────────────────


@pytest.fixture
def app_env():
    """Sauvegarde/restaure ``app_env`` dans le registre forge et expose
    un setter dédié aux tests pour basculer dev↔prod sans fuite."""
    original = forge_module._cfg.get("app_env", "dev")

    def _set(env: str) -> None:
        forge_module._cfg["app_env"] = env

    try:
        yield _set
    finally:
        forge_module._cfg["app_env"] = original


# ── 1. Forme générale du rendu en dev ───────────────────────────────────────


class TestDevHtmlEnvelope:
    def test_dev_response_est_text_html_utf8(self, app_env):
        app_env("dev")
        r = Response.debug({"message": "Bonjour"})
        assert r.content_type == "text/html; charset=utf-8"
        assert r.status == 200

    def test_dev_response_contient_doctype_html(self, app_env):
        app_env("dev")
        body = Response.debug({"message": "Bonjour"}).body.decode("utf-8")
        assert body.lower().startswith("<!doctype html>")

    def test_dev_response_contient_titre_debug_forge(self, app_env):
        app_env("dev")
        body = Response.debug({"message": "Bonjour"}).body.decode("utf-8")
        assert "Debug Forge" in body

    def test_dev_response_affiche_le_type_dict(self, app_env):
        app_env("dev")
        body = Response.debug({"message": "Bonjour"}).body.decode("utf-8")
        assert "dict" in body

    def test_dev_response_affiche_la_cle_et_la_valeur(self, app_env):
        app_env("dev")
        body = Response.debug({"message": "Bonjour"}).body.decode("utf-8")
        assert "message" in body
        assert "Bonjour" in body


# ── 2. Request.data — rendu lisible et masquage des secrets ─────────────────


class TestRequestDataRendering:
    def test_inspect_request_data_contient_method_path_params(self, app_env):
        app_env("dev")
        req = Request(_handler(path="/welcome/inspect?q=forge"))
        body = Response.debug(req.data).body.decode("utf-8")
        assert "method" in body
        assert "GET" in body
        assert "path" in body
        assert "/welcome/inspect" in body
        assert "params" in body
        assert "forge" in body

    def test_inspect_request_directement_passe_via_data(self, app_env):
        """`Response.debug(request)` déballe `request.data` (priorité 1)."""
        app_env("dev")
        req = Request(_handler(path="/welcome/inspect"))
        body = Response.debug(req).body.decode("utf-8")
        assert "method" in body
        assert "/welcome/inspect" in body

    def test_headers_sensibles_restent_masques(self, app_env):
        app_env("dev")
        req = Request(_handler(headers={"Authorization": "Bearer TOP-SECRET-VALUE"}))
        body = Response.debug(req.data).body.decode("utf-8")
        assert "TOP-SECRET-VALUE" not in body
        assert MASKED_VALUE in body

    @pytest.mark.parametrize(
        "field",
        ["password", "passwd", "secret", "token", "csrf", "api_key", "apikey"],
    )
    def test_champs_sensibles_restent_masques(self, app_env, field):
        app_env("dev")
        payload = {field: "hunter2-PLAIN", "email": "a@b.c"}
        body = Response.debug(payload).body.decode("utf-8")
        assert "hunter2-PLAIN" not in body
        assert MASKED_VALUE in body
        assert "a@b.c" in body

    def test_cookie_header_reste_masque(self, app_env):
        app_env("dev")
        req = Request(_handler(headers={"Cookie": "session_id=SECRET-COOKIE"}))
        body = Response.debug(req.data).body.decode("utf-8")
        assert "SECRET-COOKIE" not in body


# ── 3. Types natifs ─────────────────────────────────────────────────────────


class TestNativeTypeRendering:
    def test_render_dict_imbrique(self, app_env):
        app_env("dev")
        payload = {"outer": {"inner": "ok"}}
        body = Response.debug(payload).body.decode("utf-8")
        assert "outer" in body
        assert "inner" in body
        assert "ok" in body

    def test_render_list(self, app_env):
        app_env("dev")
        body = Response.debug([1, 2, 3]).body.decode("utf-8")
        assert ">1<" in body
        assert ">2<" in body
        assert ">3<" in body

    def test_render_liste_imbriquee(self, app_env):
        app_env("dev")
        body = Response.debug({"items": [{"id": 1}, {"id": 2}]}).body.decode("utf-8")
        assert "items" in body
        assert ">1<" in body
        assert ">2<" in body

    def test_render_tuple(self, app_env):
        app_env("dev")
        body = Response.debug(("a", "b")).body.decode("utf-8")
        assert ">a<" in body
        assert ">b<" in body

    def test_render_set(self, app_env):
        app_env("dev")
        body = Response.debug({"alpha"}).body.decode("utf-8")
        # un set d'un seul élément a un ordre déterministe
        assert ">alpha<" in body

    def test_render_none(self, app_env):
        app_env("dev")
        body = Response.debug({"x": None}).body.decode("utf-8")
        assert "None" in body

    def test_render_bool(self, app_env):
        app_env("dev")
        body = Response.debug({"flag": True, "off": False}).body.decode("utf-8")
        assert "True" in body
        assert "False" in body

    def test_render_int_et_float(self, app_env):
        app_env("dev")
        body = Response.debug({"n": 42, "x": 3.14}).body.decode("utf-8")
        assert "42" in body
        assert "3.14" in body


# ── 4. Objets avec `.data` ──────────────────────────────────────────────────


class TestObjectsWithData:
    def test_objet_data_dict_est_deballe(self, app_env):
        app_env("dev")

        class HasData:
            data = {"hello": "world"}

        body = Response.debug(HasData()).body.decode("utf-8")
        assert "hello" in body
        assert "world" in body

    def test_objet_data_liste_est_deballee(self, app_env):
        app_env("dev")

        class HasList:
            data = ["alpha", "beta"]

        body = Response.debug(HasList()).body.decode("utf-8")
        assert ">alpha<" in body
        assert ">beta<" in body

    def test_objet_sans_data_utilise_type_et_repr(self, app_env):
        app_env("dev")

        class Plain:
            def __repr__(self) -> str:
                return "<Plain x=1>"

        body = Response.debug(Plain()).body.decode("utf-8")
        # Le type est affiché et le repr aussi (échappé).
        assert "Plain" in body
        assert "&lt;Plain x=1&gt;" in body


# ── 5. Sécurité — échappement HTML ──────────────────────────────────────────


class TestHtmlEscape:
    def test_valeur_script_est_echappee(self, app_env):
        app_env("dev")
        body = Response.debug({"message": "<script>alert(1)</script>"}).body.decode("utf-8")
        assert "<script>alert(1)</script>" not in body
        assert "&lt;script&gt;" in body

    def test_cle_dangereuse_est_echappee(self, app_env):
        app_env("dev")
        body = Response.debug({"<img onerror=x>": "ok"}).body.decode("utf-8")
        assert "<img onerror=x>" not in body
        assert "&lt;img" in body

    def test_repr_objet_dangereux_est_echappe(self, app_env):
        app_env("dev")

        class Sneaky:
            def __repr__(self) -> str:
                return "<script>alert(2)</script>"

        body = Response.debug(Sneaky()).body.decode("utf-8")
        assert "<script>alert(2)</script>" not in body
        assert "&lt;script&gt;alert(2)&lt;/script&gt;" in body


# ── 6. Profondeur et cycles ─────────────────────────────────────────────────


class TestDepthAndCycles:
    def test_cycle_dict_ne_fait_pas_planter(self, app_env):
        app_env("dev")
        payload: dict = {"name": "root"}
        payload["self"] = payload
        body = Response.debug(payload).body.decode("utf-8")
        assert CYCLE_MARKER.replace("<", "&lt;").replace(">", "&gt;") in body

    def test_cycle_liste_ne_fait_pas_planter(self, app_env):
        app_env("dev")
        items: list = [1, 2]
        items.append(items)
        body = Response.debug(items).body.decode("utf-8")
        assert CYCLE_MARKER.replace("<", "&lt;").replace(">", "&gt;") in body

    def test_profondeur_excessive_est_tronquee(self, app_env):
        app_env("dev")
        deep: dict = {"v": "fond"}
        for _ in range(MAX_DEPTH + 3):
            deep = {"child": deep}
        body = Response.debug(deep).body.decode("utf-8")
        assert MAX_DEPTH_MARKER.replace("<", "&lt;").replace(">", "&gt;") in body
        # La valeur profonde « fond » ne doit pas être atteinte.
        assert "fond" not in body


# ── 7. Comportement en production ───────────────────────────────────────────


class TestProdRefuses:
    def test_prod_n_expose_pas_le_payload(self, app_env):
        app_env("prod")
        r = Response.debug({"message": "Bonjour", "password": "hunter2"})
        body = r.body.decode("utf-8")
        assert r.status == 404
        assert "Bonjour" not in body
        assert "hunter2" not in body
        assert "password" not in body

    def test_prod_n_expose_aucun_html_debug(self, app_env):
        app_env("prod")
        r = Response.debug({"clé": "valeur"})
        # En prod, le ContentType reste celui choisi par `Response.text(...)`.
        assert r.content_type == "text/plain; charset=utf-8"
        assert "Debug Forge" not in r.body.decode("utf-8")
        assert "<html" not in r.body.decode("utf-8").lower()

    def test_prod_masque_headers_sensibles(self, app_env):
        app_env("prod")
        req = Request(_handler(headers={"Authorization": "Bearer LEAKED"}))
        body = Response.debug(req).body.decode("utf-8")
        assert "LEAKED" not in body
        assert "Authorization" not in body


# ── 8. Pas de régression sur `Response.text`/`.html`/`.json` ────────────────


class TestOtherResponsesUnchanged:
    def test_response_text_inchange(self):
        r = Response.text("Bonjour Forge")
        assert r.content_type == "text/plain; charset=utf-8"
        assert r.body == b"Bonjour Forge"

    def test_response_html_inchange(self):
        r = Response.html("<h1>Bonjour Forge</h1>")
        assert r.content_type == "text/html; charset=utf-8"
        assert r.body == b"<h1>Bonjour Forge</h1>"

    def test_response_json_inchange(self):
        r = Response.json({"message": "ok"})
        assert r.content_type == "application/json; charset=utf-8"
        assert _json.loads(r.body.decode("utf-8")) == {"message": "ok"}


# ── 9. API du module — exports publics ──────────────────────────────────────


class TestRenderHelper:
    def test_render_debug_html_retourne_une_chaine_html(self):
        out = render_debug_html({"k": "v"})
        assert isinstance(out, str)
        assert out.lower().startswith("<!doctype html>")
        assert "Debug Forge" in out

    def test_max_depth_constante_publique_est_un_int(self):
        assert isinstance(MAX_DEPTH, int)
        assert MAX_DEPTH >= 1
