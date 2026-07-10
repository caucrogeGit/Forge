"""Garde-fou ADR-073 — make:auth honore le namespace des vues (suivi F41).

`forge make:auth` range la vue de connexion sous le namespace du projet
(`app/auth/` par défaut), comme `make:crud` pour les vues d'entités. La fonction
`make_auth()` reste plate par défaut (rétro-compat) ; la CLI résout la config.
"""
from __future__ import annotations

from pathlib import Path

from cli.security.make_auth import make_auth


def test_login_view_under_namespace(tmp_path: Path):
    make_auth(root=tmp_path, views_namespace="app")
    assert (tmp_path / "mvc" / "views" / "app" / "auth" / "login.html").is_file()
    assert not (tmp_path / "mvc" / "views" / "auth").exists()
    ctrl = (tmp_path / "mvc" / "controllers" / "auth_controller.py").read_text(encoding="utf-8")
    assert 'render("app/auth/login.html"' in ctrl
    assert 'render("auth/login.html"' not in ctrl


def test_login_routes_not_namespaced(tmp_path: Path):
    """Le namespace concerne la VUE, pas les URLs (/login reste /login)."""
    make_auth(root=tmp_path, views_namespace="app")
    routes = (tmp_path / "mvc" / "routes" / "auth_routes.py").read_text(encoding="utf-8")
    assert "/login" in routes
    assert "/app/auth" not in routes


def test_default_is_flat(tmp_path: Path):
    """make_auth() sans namespace reste à plat (rétro-compat)."""
    make_auth(root=tmp_path)
    assert (tmp_path / "mvc" / "views" / "auth" / "login.html").is_file()
    assert not (tmp_path / "mvc" / "views" / "app").exists()
    ctrl = (tmp_path / "mvc" / "controllers" / "auth_controller.py").read_text(encoding="utf-8")
    assert 'render("auth/login.html"' in ctrl
