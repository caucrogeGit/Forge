"""Garde-fou STARTER-AUTH-MFA-PROFILE-001.

Vérifie que :
1. Le starter `auth-mfa` existe et contient les fichiers MFA attendus (sans stubs).
2. Le starter `users-core-auth` (baseline sans MFA) ne contient pas de contrôleur MFA.
3. Le profil `auth-mfa` est déclaré dans SUPPORTED_PROJECT_PROFILES.

Charte principe 8 (noyau minimal, briques opt-in) et principe 1 (séparer framework
et application métier) : MFA est une feature opt-in, pas une dépendance par défaut.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STARTERS_DIR = PROJECT_ROOT / "cli" / "starters" / "data"
DEFAULT_AUTH_STARTER = STARTERS_DIR / "users-core-auth"

# Les classes TestAuthMfaStarterExists et TestAuthMfaStarterIsClean ont été
# retirées : elles inspectaient le starter supprimé `welcome-optin-mfa`.


# ── Baseline : users-core-auth n'a pas de contrôleur MFA ───────────────────

class TestDefaultAuthStarterHasNoMfaController:
    """Le starter users-core-auth (baseline) n'a pas de contrôleur MFA."""

    def test_no_mfa_challenge_controller(self):
        controller = DEFAULT_AUTH_STARTER / "files" / "mvc" / "controllers" / "mfa_challenge_controller.py"
        assert not controller.exists(), (
            "users-core-auth ne doit pas contenir mfa_challenge_controller.py. "
            "MFA est opt-in : utiliser le starter auth-mfa."
        )

    def test_auth_controller_no_forge_mvc_mfa(self):
        controller = DEFAULT_AUTH_STARTER / "files" / "mvc" / "controllers" / "auth_controller.py"
        if not controller.exists():
            return
        text = controller.read_text(encoding="utf-8")
        assert "forge_mvc_mfa" not in text, (
            "auth_controller.py de users-core-auth ne doit pas mentionner forge_mvc_mfa."
        )


# ── auth-mfa dans SUPPORTED_PROJECT_PROFILES ─────────────────────────────────

class TestAuthMfaProfileDeclared:
    """Le profil auth-mfa est déclaré dans project_profiles.py."""

    def test_auth_mfa_in_supported_profiles(self):
        from cli.project.project_profiles import SUPPORTED_PROJECT_PROFILES
        assert "auth-mfa" in SUPPORTED_PROJECT_PROFILES, (
            "auth-mfa doit être dans SUPPORTED_PROJECT_PROFILES."
        )

    def test_auth_mfa_has_description(self):
        from cli.project.project_profiles import PROJECT_PROFILE_DESCRIPTIONS
        assert "auth-mfa" in PROJECT_PROFILE_DESCRIPTIONS, (
            "auth-mfa doit avoir une description dans PROJECT_PROFILE_DESCRIPTIONS."
        )
