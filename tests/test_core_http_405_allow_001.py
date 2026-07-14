"""Tests — CORE-HTTP-405-ALLOW-001 : 405 + en-tête Allow sur mauvaise méthode.

Avant : une mauvaise méthode HTTP sur un chemin existant renvoyait 404 (le
routeur filtrant d'abord par méthode, tout non-match devenait 404). Sémantique
HTTP correcte : 405 Method Not Allowed, avec un en-tête `Allow` listant les
méthodes supportées. Un chemin réellement inconnu reste un 404.
"""
from __future__ import annotations

import pytest

from core.app.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer


def _ok(request):
    return Response(200, "ok")


@pytest.fixture
def views(tmp_path):
    errors = tmp_path / "errors"
    errors.mkdir()
    (errors / "404.html").write_text("introuvable", encoding="utf-8")
    (errors / "405.html").write_text("methode non autorisee", encoding="utf-8")
    import core.forge as forge

    forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    return tmp_path


class _FakeRequest:
    def __init__(self, method: str, path: str) -> None:
        self.method = method
        self.original_method = method
        self.path = path
        self.route_params: dict[str, str] = {}


class TestAllowedMethods:
    def test_chemin_connu_liste_les_methodes(self):
        router = Router()
        router.add("GET", "/clients", _ok)
        router.add("POST", "/clients", _ok)
        assert router.allowed_methods("/clients") == ["GET", "POST"]

    def test_chemin_dynamique(self):
        router = Router()
        router.add("GET", "/clients/{id}", _ok)
        router.add("DELETE", "/clients/{id}", _ok)
        assert router.allowed_methods("/clients/42") == ["DELETE", "GET"]

    def test_chemin_inconnu_liste_vide(self):
        router = Router()
        router.add("GET", "/clients", _ok)
        assert router.allowed_methods("/introuvable") == []


class TestDispatch405:
    def test_mauvaise_methode_retourne_405(self, views):
        router = Router()
        router.add("GET", "/clients", _ok, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        resp = app.dispatch(_FakeRequest("POST", "/clients"))
        assert resp.status == 405

    def test_405_porte_l_entete_allow(self, views):
        router = Router()
        router.add("GET", "/clients", _ok, public=True)
        router.add("PUT", "/clients", _ok, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        resp = app.dispatch(_FakeRequest("POST", "/clients"))
        assert resp.status == 405
        assert resp.headers.get("Allow") == "GET, PUT"

    def test_chemin_inconnu_reste_404(self, views):
        router = Router()
        router.add("GET", "/clients", _ok, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        resp = app.dispatch(_FakeRequest("GET", "/introuvable"))
        assert resp.status == 404

    def test_bonne_methode_atteint_le_handler(self, views):
        router = Router()
        router.add("GET", "/clients", _ok, public=True)
        app = Application(router, middlewares=[], api_routes_module=None)
        resp = app.dispatch(_FakeRequest("GET", "/clients"))
        assert resp.status == 200
