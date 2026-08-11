"""FORGE-5 — `forge make:auth` scaffolde le flux de connexion.

Le cœur redirige vers `/login` (codé en dur) et fournit le backend auth, mais rien
ne scaffoldait la route/le contrôleur/la vue de login. `make:auth` génère un
contrôleur + une vue (write-if-new) et affiche les routes à ajouter (Forge affiche).
"""
from __future__ import annotations

import ast
from pathlib import Path

from cli.security import make_auth as ma
from cli.security.make_auth import (
    AUTH_CONTROLLER,
    AUTH_USER_MODEL,
    AUTH_NAV_ANCHOR,
    AUTH_NAV_BLOCK,
    AUTH_ROUTES_FILE,
    make_auth,
)


def test_genere_controleur_et_vue(tmp_path: Path):
    result = make_auth(root=tmp_path)
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    view = tmp_path / "mvc" / "views" / "auth" / "login.html"
    routes = tmp_path / "mvc" / "routes" / "auth_routes.py"
    assert ctrl.is_file() and view.is_file() and routes.is_file()
    assert ctrl.as_posix() in result.created
    assert view.as_posix() in result.created
    assert routes.as_posix() in result.created


def test_write_if_new_avertit_sur_existant_divergent(tmp_path: Path):
    # CLI-SCAFFOLD-PRIMITIVE-001 : existant au contenu différent → averti, jamais écrasé.
    ctrl = tmp_path / "mvc" / "controllers" / "auth_controller.py"
    ctrl.parent.mkdir(parents=True)
    ctrl.write_text("# mon contrôleur\n", encoding="utf-8")
    result = make_auth(root=tmp_path)
    assert ctrl.read_text(encoding="utf-8") == "# mon contrôleur\n"  # jamais écrasé
    assert ctrl.as_posix() in result.warned


def test_controleur_cable_sur_le_backend_auth():
    # Flux : authenticate_user (loader users), login_user, régénération anti-fixation.
    assert "authenticate_user(login, password, load_user_by_login)" in AUTH_CONTROLLER
    assert "login_user(request, user)" in AUTH_CONTROLLER
    assert "regenerate_session(session_id)" in AUTH_CONTROLLER
    assert "logout_user(request)" in AUTH_CONTROLLER
    # MAKE-AUTH-MODEL-LAYER-001 : le SQL a quitté le contrôleur pour le modèle.
    assert "FROM users WHERE login = ?" not in AUTH_CONTROLLER
    assert "from mvc.models.user_model import load_user_by_login" in AUTH_CONTROLLER
    assert 'BaseController.redirect("/login")' in AUTH_CONTROLLER


def test_controleur_genere_est_anti_bruteforce():
    # Principe §7 « sécuriser par défaut » : le /login scaffoldé plafonne les
    # tentatives par IP (vérification avant auth + enregistrement sur échec).
    assert "is_login_rate_limited(request.ip)" in AUTH_CONTROLLER
    assert "record_login_attempt(request.ip)" in AUTH_CONTROLLER
    assert (
        "from core.auth.rate_limit import is_login_rate_limited, record_login_attempt"
        in AUTH_CONTROLLER
    )


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


# ── Bouton nav Connexion / Déconnexion (injection chirurgicale) ──────────────

def _nav_with_anchor(tmp_path: Path, extra: str = "") -> Path:
    nav = tmp_path / "mvc" / "views" / "partials" / "nav.html"
    nav.parent.mkdir(parents=True, exist_ok=True)
    nav.write_text(f"{AUTH_NAV_ANCHOR}\n{extra}", encoding="utf-8")
    return nav


def test_bloc_bouton_conditionnel_login_logout():
    # Visiteur -> Connexion (/login) ; connecté -> Déconnexion (POST /logout).
    assert "is_authenticated" in AUTH_NAV_BLOCK
    assert '"Connexion"' in AUTH_NAV_BLOCK and 'href="/login"' in AUTH_NAV_BLOCK
    assert '"Déconnexion"' in AUTH_NAV_BLOCK and 'action="/logout"' in AUTH_NAV_BLOCK
    assert 'name="csrf_token"' in AUTH_NAV_BLOCK


def test_injecte_bouton_dans_nav_et_preserve_les_liens(tmp_path: Path):
    nav = _nav_with_anchor(tmp_path, '<a href="/classes">Classes</a>\n')
    result = make_auth(root=tmp_path)
    content = nav.read_text(encoding="utf-8")
    assert "forge:auth-nav:start" in content              # bouton injecté
    assert '<a href="/classes">Classes</a>' in content    # lien utilisateur préservé
    assert nav.as_posix() in result.modified
    # Plus de fichier auth_nav.html séparé.
    assert not (tmp_path / "mvc" / "views" / "partials" / "auth_nav.html").exists()


def test_injection_nav_idempotente(tmp_path: Path):
    nav = _nav_with_anchor(tmp_path)
    make_auth(root=tmp_path)
    result = make_auth(root=tmp_path)
    assert nav.read_text(encoding="utf-8").count("forge:auth-nav:start") == 1
    assert nav.as_posix() in result.skipped


def test_nav_absente_est_creee_avec_bouton(tmp_path: Path):
    result = make_auth(root=tmp_path)
    nav = tmp_path / "mvc" / "views" / "partials" / "nav.html"
    assert nav.is_file()
    assert nav.as_posix() in result.created
    assert "forge:auth-nav:start" in nav.read_text(encoding="utf-8")


def test_nav_sans_ancrage_ne_reecrit_pas_et_affiche(tmp_path: Path):
    nav = tmp_path / "mvc" / "views" / "partials" / "nav.html"
    nav.parent.mkdir(parents=True)
    nav.write_text("<a href='/x'>X</a>\n", encoding="utf-8")
    result = make_auth(root=tmp_path)
    assert result.nav_needs_manual is True
    assert nav.read_text(encoding="utf-8") == "<a href='/x'>X</a>\n"  # inchangé (§7)


def test_skeleton_nav_a_l_ancrage_injecte_par_base(tmp_path: Path):
    # base.html inclut partials/nav.html ; le squelette livre nav.html avec l'ancrage
    # où make:auth injecte le bouton (sans éditer base.html).
    views = Path("skeleton/data/mvc/views")
    base = (views / "layouts" / "base.html").read_text(encoding="utf-8")
    nav = (views / "partials" / "nav.html").read_text(encoding="utf-8")
    assert '{% include "partials/nav.html" ignore missing %}' in base
    assert AUTH_NAV_ANCHOR in nav


def test_render_injecte_is_authenticated():
    # Contrat dont dépend le bouton nav : BaseController.render expose is_authenticated
    # à tout template (comme csrf_token).
    src = Path("core/mvc/controller/base_controller.py").read_text(encoding="utf-8")
    assert '"is_authenticated"' in src
    assert "is_authenticated(request)" in src


def test_le_loader_sql_vit_dans_le_modele(tmp_path: Path):
    """MAKE-AUTH-MODEL-LAYER-001 : le contrôleur appelle, le modèle interroge.

    Le scaffold d'authentification portait sa requête SQL dans le contrôleur,
    en contradiction avec la séparation que `make:crud` produit et que la
    documentation Forge enseigne. Un générateur ne peut pas enseigner une
    doctrine qu'il enfreint lui-même.
    """
    assert "FROM users WHERE login = ?" in AUTH_USER_MODEL
    assert "def load_user_by_login" in AUTH_USER_MODEL
    assert "from core.database.db import fetch_one" in AUTH_USER_MODEL

    result = make_auth(root=tmp_path)
    modele = tmp_path / "mvc" / "models" / "user_model.py"
    assert modele.as_posix() in result.created
    ast.parse(modele.read_text(encoding="utf-8"))


def test_aucun_sql_dans_le_controleur_genere(tmp_path: Path):
    """Garde-fou de cause : le contrôleur n'accède plus à la base."""
    make_auth(root=tmp_path)
    controleur = (tmp_path / "mvc" / "controllers" / "auth_controller.py").read_text(
        encoding="utf-8"
    )

    for interdit in ("SELECT", "fetch_one", "core.database"):
        assert interdit not in controleur, (
            f"le contrôleur d'authentification généré contient encore « {interdit} »"
        )
