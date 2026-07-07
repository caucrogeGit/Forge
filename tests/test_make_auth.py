"""FORGE-5 — `forge make:auth` scaffolde le flux de connexion.

Le cœur redirige vers `/login` (codé en dur) et fournit le backend auth, mais rien
ne scaffoldait la route/le contrôleur/la vue de login. `make:auth` génère un
contrôleur + une vue (write-if-new) et affiche les routes à ajouter (Forge affiche).
"""
from __future__ import annotations

import ast
from pathlib import Path

from cli.security import make_auth as ma
from cli.security.make_auth import AUTH_CONTROLLER, AUTH_ROUTES_FILE, make_auth


def test_genere_controleur_et_vue(tmp_path: Path):
    result = make_auth(root=tmp_path)
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    view = tmp_path / "mvc" / "views" / "auth" / "login.html"
    routes = tmp_path / "mvc" / "routes" / "auth_routes.py"
    assert ctrl.is_file() and view.is_file() and routes.is_file()
    assert ctrl.as_posix() in result.created
    assert view.as_posix() in result.created
    assert routes.as_posix() in result.created


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


def test_routes_login_public_logout(tmp_path: Path):
    # ADR-068 : les routes vivent dans mvc/routes/auth_routes.py ; le bloc affiché
    # ne fait que brancher.
    routes = (tmp_path / "mvc" / "routes" / "auth_routes.py")
    make_auth(root=tmp_path)
    assert routes.is_file()
    content = routes.read_text(encoding="utf-8")
    assert '"GET", "/login"' in content and '"POST", "/login"' in content
    assert "public=True" in content                     # login accessible sans auth
    assert '"POST", "/logout"' in content
    assert "def register_auth_routes(router" in AUTH_ROUTES_FILE


def test_bloc_branchement(tmp_path: Path):
    block = make_auth(root=tmp_path).route_block
    assert "from mvc.routes.auth_routes import register_auth_routes" in block
    assert "register_auth_routes(router)" in block


def test_main_affiche_routes_et_prerequis(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    ma.main(["make:auth"])
    out = capsys.readouterr().out
    assert "Branchement à ajouter dans mvc/routes/__init__.py" in out
    assert "register_auth_routes" in out
    assert "forge auth:init" in out
    assert "[CREE]" in out
