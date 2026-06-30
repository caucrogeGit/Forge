"""Garde-fou SEC-HTML-RAW-TRAVERSAL-001 : html(..., raw=True) reste sous views_dir.

`html(template, raw=True)` sert un fichier brut depuis le dossier des vues. Sans
contrôle, un `template` contenant « ../ » (ou un chemin absolu) sortirait du
dossier et lirait un fichier arbitraire. On vérifie ici que la traversée est
refusée (le contenu hors-dossier ne fuit jamais) et que le cas légitime marche.
"""
from __future__ import annotations

import pytest

import core.forge as forge
from core.http.helpers import html
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer


class TestHtmlRawTraversal:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.views = tmp_path / "views"
        self.views.mkdir()
        forge._cfg["views_dir"] = str(self.views)
        template_manager.register(Jinja2Renderer(str(self.views)))
        # Fichier sensible volontairement placé HORS du dossier des vues.
        self.secret = tmp_path / "secret.txt"
        self.secret.write_text("TOP-SECRET-CONTENT")

    def test_traversal_relatif_bloque(self):
        resp = html("../secret.txt", raw=True)
        assert b"TOP-SECRET-CONTENT" not in resp.body

    def test_chemin_absolu_bloque(self):
        resp = html(str(self.secret), raw=True)
        assert b"TOP-SECRET-CONTENT" not in resp.body

    def test_fichier_legitime_toujours_servi(self):
        (self.views / "ok.txt").write_text("CONTENU-OK")
        resp = html("ok.txt", raw=True)
        assert resp.body == b"CONTENU-OK"
