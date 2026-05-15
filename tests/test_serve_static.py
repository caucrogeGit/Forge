"""
Tests de _is_safe_static_path (app.py) — protection contre le path traversal.
"""
import os
import pytest

import app
from core.http.response import Response

from app import _is_safe_static_path


class TestIsStaticPathSafe:
    def test_chemin_valide_dans_static(self, tmp_path):
        static = str(tmp_path / "static")
        filepath = str(tmp_path / "static" / "style.css")
        assert _is_safe_static_path(static, filepath) is True

    def test_chemin_sous_repertoire_valide(self, tmp_path):
        static = str(tmp_path / "static")
        filepath = str(tmp_path / "static" / "img" / "logo.png")
        assert _is_safe_static_path(static, filepath) is True

    def test_traversal_remonte_hors_static(self, tmp_path):
        static = str(tmp_path / "static")
        # realpath d'un traversal atterrit hors de static/
        filepath = str(tmp_path / "etc" / "passwd")
        assert _is_safe_static_path(static, filepath) is False

    def test_dossier_sibling_commence_meme_prefix(self, tmp_path):
        # /static est préfixe de /staticold — startswith aurait accepté, commonpath refuse
        static = str(tmp_path / "static")
        filepath = str(tmp_path / "staticold" / "hack.css")
        assert _is_safe_static_path(static, filepath) is False

    def test_static_dir_lui_meme_refuse(self, tmp_path):
        # Le répertoire static/ lui-même : commonpath == static_dir, mais c'est un dossier
        # _is_safe_static_path retourne True ici (la protection fichier/dossier est en aval)
        static = str(tmp_path / "static")
        assert _is_safe_static_path(static, static) is True

    def test_chemin_parent_refuse(self, tmp_path):
        static = str(tmp_path / "static")
        filepath = str(tmp_path)
        assert _is_safe_static_path(static, filepath) is False

    @pytest.mark.skipif(os.name != "nt", reason="ValueError uniquement sur chemins Windows multi-drive")
    def test_value_error_retourne_false(self):
        assert _is_safe_static_path("C:\\static", "D:\\other\\file.css") is False


class _StaticHandler:
    def __init__(self):
        self.responses = []

    def _send_response(self, response):
        self.responses.append(response)


def test_static_directory_retourne_404_pas_500(monkeypatch, tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    monkeypatch.setattr(app, "STATIC_DIR", str(static_dir))
    monkeypatch.setattr(app, "_html", lambda template, status: Response(status, template))

    handler = _StaticHandler()
    app.RequestHandler._serve_static(handler, "/static/")

    assert handler.responses[-1].status == 404


def test_static_file_reel_reste_servi(monkeypatch, tmp_path):
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "style.css").write_text("body { color: black; }", encoding="utf-8")
    monkeypatch.setattr(app, "STATIC_DIR", str(static_dir))

    handler = _StaticHandler()
    app.RequestHandler._serve_static(handler, "/static/style.css")

    response = handler.responses[-1]
    assert response.status == 200
    assert response.content_type == "text/css"
    assert b"color: black" in response.body
