"""FORGE-5 — `forge make:auth` scaffolde le flux de connexion.

Le cœur redirige vers `/login` (codé en dur) et fournit le backend auth, mais rien
ne scaffoldait la route/le contrôleur/la vue de login. `make:auth` génère un
contrôleur + une vue (write-if-new) et affiche les routes à ajouter (Forge affiche).
"""
from __future__ import annotations

import ast
from pathlib import Path

from cli.security import make_auth as ma
from cli.security.make_auth import AUTH_CONTROLLER, make_auth


def test_genere_controleur_et_vue(tmp_path: Path):
    result = make_auth(root=tmp_path)
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    view = tmp_path / "mvc" / "views" / "auth" / "login.html"
    assert ctrl.is_file() and view.is_file()
    assert ctrl.as_posix() in result.created
    assert view.as_posix() in result.created


def test_write_if_new_preserve_l_existant(tmp_path: Path):
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    ctrl.parent.mkdir(parents=True)
    ctrl.write_text("# mon contrôleur\n", encoding="utf-8")
    result = make_auth(root=tmp_path)
    assert ctrl.read_text(encoding="utf-8") == "# mon contrôleur\n"  # préservé
    assert ctrl.as_posix() in result.skipped


def test_controleur_cable_sur_le_backend_auth():
    # Flux : authenticate_user (loader users), login_user, régénération anti-fixation.
    assert "authenticate_user(email, password, load_user_by_email)" in AUTH_CONTROLLER
    assert "login_user(request, user)" in AUTH_CONTROLLER
    assert "regenerate_session(session_id)" in AUTH_CONTROLLER
    assert "logout_user(request)" in AUTH_CONTROLLER
    assert "FROM users WHERE email = ?" in AUTH_CONTROLLER
    assert 'BaseController.redirect("/login")' in AUTH_CONTROLLER


def test_controleur_genere_est_du_python_valide():
    ast.parse(AUTH_CONTROLLER)  # ne lève pas


def test_bloc_routes_login_public_logout(tmp_path: Path, capsys):
    result = make_auth(root=tmp_path)
    block = result.route_block
    assert '"GET",  "/login"' in block and '"POST", "/login"' in block
    assert 'public=True' in block                     # login accessible sans auth
    assert '"POST", "/logout"' in block
    assert "AuthController" in block


def test_main_affiche_routes_et_prerequis(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    ma.main(["make:auth"])
    out = capsys.readouterr().out
    assert "Routes à ajouter dans mvc/routes.py" in out
    assert "forge auth:init" in out
    assert "[CREE]" in out
