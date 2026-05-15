"""AUTH-CLI-LOGIN-E2E-TEST-001 — Flux CLI Auth → login contrôleur par défaut.

Scénario testé :
1. Hash Argon2id généré comme le ferait `forge auth:user:create` (core.auth.password.hash_password).
2. Hash injecté dans la structure retournée par auth_model (mock de get_user_by_login).
3. POST /login via AuthController.login avec le bon mot de passe.
4. Vérification : redirect 302 vers / → session authentifiée.
5. Vérification négative : mauvais mot de passe → 200 + message d'erreur.

Note architecturale : la CLI Auth (table `users`) et le contrôleur par défaut (table
`utilisateur`) n'utilisent pas encore la même table. Ce test valide que le format de hash
produit par la CLI (Argon2id) est bien accepté par _check_password du contrôleur, via un
mock de get_user_by_login. Le flux base-de-données complet sera couvert dans STARTERS-AUTH-AUDIT-001.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch

import core.forge as _forge
from core.auth.password import hash_password
from core.security.session import create_session, get_session
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from tests.fake_request import FakeRequest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _views(tmp_path):
    """Templates minimaux requis par AuthController."""
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth" / "partials").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "auth" / "login.html").write_text(
        "LOGIN csrf={{ csrf_token }} erreur={{ erreur }}", encoding="utf-8"
    )
    (tmp_path / "auth" / "partials" / "erreur.html").write_text(
        "<span>{{ message }}</span>", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "429.html").write_text("429", encoding="utf-8")
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    yield
    _forge._cfg["views_dir"] = str(tmp_path)


def _make_user(password_hash: str) -> dict:
    """Construit une structure utilisateur compatible avec get_user_by_login."""
    return {
        "UtilisateurId": 1,
        "Login": "user@example.com",
        "PasswordHash": password_hash,
        "Actif": 1,
        "Email": "user@example.com",
        "Prenom": "Test",
        "Nom": "User",
        "roles": [],
    }


def _post_login(password: str, user: dict) -> object:
    """Simule une requête POST /login vers AuthController."""
    sid  = create_session()
    sess = get_session(sid)
    req  = FakeRequest(
        "POST", "/login",
        body={"login": user["Login"], "password": password,
              "csrf_token": sess["csrf_token"]},
        session_id=sid,
    )
    with (
        patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
        patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
    ):
        return AuthController.login(req)


# ── Format du hash ────────────────────────────────────────────────────────────

def test_cli_login_e2e_uses_argon2_hash_format():
    """hash_password produit bien un hash Argon2id ($argon2id$...)."""
    h = hash_password("MonMotDePasse99")
    assert h.startswith("$argon2id$"), f"Hash inattendu : {h[:30]}"


# ── Flux complet : bon mot de passe ───────────────────────────────────────────

def test_cli_created_argon2_user_can_login_with_default_controller():
    """Un utilisateur créé avec hash_password (CLI Auth) peut se connecter
    via le contrôleur par défaut après AUTH-DEFAULT-ALIGN-001."""
    password = "MonMotDePasse99"
    password_hash = hash_password(password)
    user = _make_user(password_hash)

    resp = _post_login(password, user)

    assert resp.status == 302, f"Attendu 302, obtenu {resp.status}"
    assert resp.headers.get("Location") == "/", (
        f"Attendu redirect vers /, obtenu : {resp.headers.get('Location')}"
    )


def test_cli_created_argon2_user_login_sets_new_session_cookie():
    """Le login réussi définit un nouveau cookie de session."""
    password = "AutreMotDePasse1"
    user = _make_user(hash_password(password))

    resp = _post_login(password, user)

    assert "__Host-session_id=" in resp.headers.get("Set-Cookie", "")


# ── Flux complet : mauvais mot de passe ───────────────────────────────────────

def test_cli_created_argon2_user_cannot_login_with_wrong_password():
    """Un utilisateur Argon2id ne peut pas se connecter avec un mauvais mot de passe."""
    user = _make_user(hash_password("MonMotDePasse99"))

    resp = _post_login("mauvaismdp", user)

    assert resp.status == 200, f"Attendu 200 (formulaire erreur), obtenu {resp.status}"
    assert b"Identifiant ou mot de passe incorrect" in resp.body


def test_cli_created_argon2_user_wrong_password_shows_error_message():
    """Le message d'erreur est affiché en cas de mauvais mot de passe."""
    user = _make_user(hash_password("secret123"))

    resp = _post_login("secret_wrong", user)

    assert resp.status == 200
    assert b"incorrect" in resp.body.lower() or b"erreur" in resp.body.lower()


# ── Isolation : verify_password est le chemin principal ──────────────────────

def test_cli_login_e2e_does_not_call_verify_password_legacy_for_argon2_hash():
    """Pour un hash Argon2id, verify_password_legacy (PBKDF2) ne doit pas être
    invoqué — verify_password (Argon2id) suffit."""
    password = "SecretArgon2"
    user = _make_user(hash_password(password))

    with (
        patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
        patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
        patch("mvc.controllers.auth_controller.verify_password_legacy") as mock_pbkdf2,
    ):
        sid  = create_session()
        sess = get_session(sid)
        req  = FakeRequest(
            "POST", "/login",
            body={"login": user["Login"], "password": password,
                  "csrf_token": sess["csrf_token"]},
            session_id=sid,
        )
        resp = AuthController.login(req)

    assert resp.status == 302
    mock_pbkdf2.assert_not_called()
