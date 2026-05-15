"""AUTH-HASH-MIGRATION-001 — Migration PBKDF2 → Argon2id après login réussi.

Vérifie que :
- un login réussi avec hash PBKDF2 legacy (<sel_hex>:<hash_hex>) déclenche une migration ;
- un login réussi avec hash PBKDF2 versionné (pbkdf2_sha256$…) déclenche une migration ;
- un login réussi avec hash Argon2id ne déclenche pas de migration inutile ;
- un mauvais mot de passe n'entraîne aucune migration ;
- une erreur de persistance ne bloque pas le login.
"""
from __future__ import annotations

import hashlib
import os
from unittest.mock import patch

import pytest

import core.forge as _forge
from core.auth.password import hash_password
from core.security.hashing import LEGACY_ITERATIONS
from core.security.session import create_session, get_session
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from tests.fake_request import FakeRequest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _views(tmp_path):
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(password_hash: str) -> dict:
    return {
        "UtilisateurId": 42,
        "Login": "legacyuser",
        "PasswordHash": password_hash,
        "Actif": 1,
        "Email": "legacy@example.com",
        "Prenom": "Legacy",
        "Nom": "User",
        "roles": [],
    }


def _make_legacy_hash(password: str) -> str:
    """Génère un hash au format legacy <sel_hex>:<hash_hex> (avant SECURITY-PBKDF2-HARDENING-001)."""
    sel = os.urandom(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, LEGACY_ITERATIONS)
    return sel.hex() + ":" + hash_.hex()


def _make_pbkdf2_versioned_hash(password: str, iterations: int = 600_000) -> str:
    """Génère un hash PBKDF2 au format versionné (sans utiliser l'API supprimée)."""
    sel = os.urandom(16)
    hash_ = hashlib.pbkdf2_hmac("sha256", password.encode(), sel, iterations)
    return f"pbkdf2_sha256${iterations}${sel.hex()}${hash_.hex()}"


def _post_login(password: str, user: dict):
    """Simule POST /login. Retourne (response, mock_update_password_hash)."""
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
        patch("mvc.controllers.auth_controller.update_password_hash") as mock_update,
    ):
        resp = AuthController.login(req)
    return resp, mock_update


# ── Migration hash PBKDF2 legacy (<sel_hex>:<hash_hex>) ──────────────────────

class TestMigrationHashLegacy:

    def test_login_reussi_legacy_redirige(self):
        password = "ancienmdp"
        user = _make_user(_make_legacy_hash(password))
        resp, _ = _post_login(password, user)
        assert resp.status == 302

    def test_login_legacy_declenche_migration(self):
        password = "ancienmdp"
        user = _make_user(_make_legacy_hash(password))
        _, mock_update = _post_login(password, user)
        mock_update.assert_called_once()

    def test_login_legacy_migre_vers_argon2id(self):
        password = "ancienmdp"
        user = _make_user(_make_legacy_hash(password))
        _, mock_update = _post_login(password, user)
        user_id, new_hash = mock_update.call_args[0]
        assert user_id == 42
        assert new_hash.startswith("$argon2id$")

    def test_login_legacy_migre_avec_bon_id(self):
        password = "ancienmdp"
        user = _make_user(_make_legacy_hash(password))
        _, mock_update = _post_login(password, user)
        user_id, _ = mock_update.call_args[0]
        assert user_id == user["UtilisateurId"]


# ── Migration hash PBKDF2 versionné (pbkdf2_sha256$600000$…) ─────────────────

class TestMigrationHashPbkdf2Versionne:

    def test_login_reussi_pbkdf2_versionne_redirige(self):
        password = "ancienmdp"
        user = _make_user(_make_pbkdf2_versioned_hash(password))
        resp, _ = _post_login(password, user)
        assert resp.status == 302

    def test_login_pbkdf2_versionne_declenche_migration(self):
        password = "ancienmdp"
        user = _make_user(_make_pbkdf2_versioned_hash(password))
        _, mock_update = _post_login(password, user)
        mock_update.assert_called_once()

    def test_login_pbkdf2_versionne_migre_vers_argon2id(self):
        password = "ancienmdp"
        user = _make_user(_make_pbkdf2_versioned_hash(password))
        _, mock_update = _post_login(password, user)
        _, new_hash = mock_update.call_args[0]
        assert new_hash.startswith("$argon2id$")


# ── Pas de migration pour un hash Argon2id ────────────────────────────────────

class TestPasMigrationArgon2id:

    def test_login_argon2id_reussi_redirige(self):
        password = "modernmdp"
        user = _make_user(hash_password(password))
        resp, _ = _post_login(password, user)
        assert resp.status == 302

    def test_login_argon2id_ne_declenche_pas_migration(self):
        password = "modernmdp"
        user = _make_user(hash_password(password))
        _, mock_update = _post_login(password, user)
        mock_update.assert_not_called()


# ── Pas de migration en cas d'échec ───────────────────────────────────────────

class TestPasMigrationEchecLogin:

    def test_mauvais_mdp_legacy_refuse(self):
        user = _make_user(_make_legacy_hash("bonmdp"))
        resp, _ = _post_login("mauvaismdp", user)
        assert resp.status == 200

    def test_mauvais_mdp_legacy_ne_migre_pas(self):
        user = _make_user(_make_legacy_hash("bonmdp"))
        _, mock_update = _post_login("mauvaismdp", user)
        mock_update.assert_not_called()

    def test_mauvais_mdp_argon2id_ne_migre_pas(self):
        user = _make_user(hash_password("bonmdp"))
        _, mock_update = _post_login("mauvaismdp", user)
        mock_update.assert_not_called()

    def test_mauvais_mdp_pbkdf2_versionne_ne_migre_pas(self):
        user = _make_user(_make_pbkdf2_versioned_hash("bonmdp"))
        _, mock_update = _post_login("mauvaismdp", user)
        mock_update.assert_not_called()


# ── Erreur de persistance non bloquante ───────────────────────────────────────

class TestErreurMigrationNonBloquante:

    def test_erreur_db_login_reussit_quand_meme(self):
        password = "ancienmdp"
        user = _make_user(_make_legacy_hash(password))
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
            patch("mvc.controllers.auth_controller.update_password_hash",
                  side_effect=Exception("DB indisponible")),
        ):
            resp = AuthController.login(req)

        assert resp.status == 302

    def test_erreur_db_ne_masque_pas_le_mdp(self):
        """En cas d'échec de migration, le mot de passe ne doit pas apparaître dans la réponse."""
        password = "ancienmdp_secret"
        user = _make_user(_make_legacy_hash(password))
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
            patch("mvc.controllers.auth_controller.update_password_hash",
                  side_effect=Exception("DB error")),
        ):
            resp = AuthController.login(req)

        assert password.encode() not in resp.body
        assert resp.status == 302
