"""Garde-fou STARTER-LANG-NORMALIZE-001.

Vérifie que les starters respectent la convention de frontière linguistique :
- le schéma SQL reste français (noms de colonnes) ;
- les variables Python et les clés de contexte de template utilisent des noms
  canoniques anglais ou normalisés ;
- les API dépréciées (get_user, authenticate_session) ne sont pas utilisées ;
- les starters actifs exposent build_auth_user() pour l'isolation du mapping SQL.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STARTERS = PROJECT_ROOT / "forge_cli" / "starters" / "data"

UTILISATEURS_AUTH = STARTERS / "utilisateurs-auth" / "files"
AUTH_MFA = STARTERS / "welcome-optin-mfa" / "files"


# ── utilisateurs-auth : référence ─────────────────────────────────────────────

class TestUtilisateursAuthReference:

    def test_build_auth_user_present(self):
        src = (UTILISATEURS_AUTH / "mvc" / "models" / "auth_model.py").read_text()
        assert "def build_auth_user" in src

    def test_get_user_by_id_present(self):
        src = (UTILISATEURS_AUTH / "mvc" / "models" / "auth_model.py").read_text()
        assert "def get_user_by_id" in src

    def test_no_inline_auth_user(self):
        src = (UTILISATEURS_AUTH / "mvc" / "controllers" / "auth_controller.py").read_text()
        assert "AuthUser(" not in src


# ── welcome-optin-mfa ─────────────────────────────────────────────────────────

class TestAuthMfaController:

    def test_no_inline_auth_user(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "auth_controller.py").read_text()
        assert "AuthUser(" not in src

    def test_build_auth_user_imported(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "auth_controller.py").read_text()
        assert "build_auth_user" in src


class TestMfaChallengeController:

    def test_no_deprecated_authenticate_session(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "mfa_challenge_controller.py").read_text()
        assert "authenticate_session" not in src

    def test_uses_login_user(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "mfa_challenge_controller.py").read_text()
        assert "login_user" in src

    def test_uses_normalize_auth_user(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "mfa_challenge_controller.py").read_text()
        assert "normalize_auth_user" in src

    def test_default_finalize_receives_request(self):
        src = (AUTH_MFA / "mvc" / "controllers" / "mfa_challenge_controller.py").read_text()
        assert "_default_finalize(user_id, session_id, request)" in src
