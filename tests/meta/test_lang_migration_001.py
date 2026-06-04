"""Tests LANG-MIGRATION-001 — API publique de Forge en anglais (ADR-003).

Vérifie que :
- les nouveaux noms anglais sont disponibles et appelables ;
- les anciens noms français ont disparu ;
- aucun fichier hors ce module n'appelle les anciens noms ;
- le paramètre utilisateur_id a bien été renommé user_id dans auth_model.
"""
from __future__ import annotations

import importlib
import inspect
import subprocess

import pytest

pytestmark = pytest.mark.meta

# ── TestNewApiAvailable ────────────────────────────────────────────────────────

class TestNewApiAvailable:
    """Les nouveaux symboles anglais sont importables et du bon type."""

    # core.security.session

    def test_session_duration_constant(self):
        from core.security.session import SESSION_DURATION
        assert isinstance(SESSION_DURATION, int)

    def test_create_session_callable(self):
        from core.security.session import create_session
        assert callable(create_session)

    def test_delete_session_callable(self):
        from core.security.session import delete_session
        assert callable(delete_session)

    def test_regenerate_session_callable(self):
        from core.security.session import regenerate_session
        assert callable(regenerate_session)

    def test_authenticate_session_callable(self):
        from core.security.session import authenticate_session
        assert callable(authenticate_session)

    def test_is_authenticated_callable(self):
        from core.security.session import is_authenticated
        assert callable(is_authenticated)

    def test_get_user_callable(self):
        from core.security.session import get_user
        assert callable(get_user)

    def test_user_has_role_callable(self):
        from core.security.session import user_has_role
        assert callable(user_has_role)

    # core.security.hashing

    def test_max_attempts_constant(self):
        from core.security.hashing import MAX_ATTEMPTS
        assert isinstance(MAX_ATTEMPTS, int)

    def test_rate_limit_window_constant(self):
        from core.security.hashing import RATE_LIMIT_WINDOW
        assert isinstance(RATE_LIMIT_WINDOW, int)

    def test_verify_password_legacy_callable(self):
        from core.security.hashing import verify_password_legacy
        assert callable(verify_password_legacy)

    def test_record_attempt_callable(self):
        from core.security.hashing import record_attempt
        assert callable(record_attempt)

    def test_is_rate_limited_callable(self):
        from core.security.hashing import is_rate_limited
        assert callable(is_rate_limited)

    # core.uploads.rate_limit

    def test_upload_rate_limit_window_constant(self):
        from forge_mvc_files.rate_limit import UPLOAD_RATE_LIMIT_WINDOW
        assert isinstance(UPLOAD_RATE_LIMIT_WINDOW, int)

    def test_is_upload_rate_limited_callable(self):
        from forge_mvc_files.rate_limit import is_upload_rate_limited
        assert callable(is_upload_rate_limited)

    def test_record_upload_attempt_callable(self):
        from forge_mvc_files.rate_limit import record_upload_attempt
        assert callable(record_upload_attempt)

    # mvc.models.auth_model

    def test_update_password_hash_callable(self):
        from mvc.models.auth_model import update_password_hash
        assert callable(update_password_hash)


# ── TestOldFrenchApiRemoved ────────────────────────────────────────────────────

_OLD_SYMBOLS = [
    ("core.security.session",  "DUREE_SESSION"),
    ("core.security.session",  "creer_session"),
    ("core.security.session",  "supprimer_session"),
    ("core.security.session",  "regenerer_session"),
    ("core.security.session",  "authentifier_session"),
    ("core.security.session",  "est_authentifie"),
    ("core.security.session",  "get_utilisateur"),
    ("core.security.session",  "utilisateur_a_role"),
    ("core.security.hashing",  "MAX_TENTATIVES"),
    ("core.security.hashing",  "FENETRE_SECONDES"),
    ("core.security.hashing",  "verifier_mot_de_passe"),
    ("core.security.hashing",  "enregistrer_tentative"),
    ("core.security.hashing",  "est_limite"),
    ("forge_mvc_files.rate_limit", "UPLOAD_FENETRE_SECONDES"),
    ("forge_mvc_files.rate_limit", "est_limite_upload"),
    ("forge_mvc_files.rate_limit", "enregistrer_upload"),
]


@pytest.mark.parametrize("module_path,symbol", _OLD_SYMBOLS)
class TestOldFrenchApiRemoved:
    """Les anciens noms français ne sont plus exportés par leurs modules."""

    def test_symbol_absent(self, module_path, symbol):
        mod = importlib.import_module(module_path)
        assert not hasattr(mod, symbol), (
            f"{module_path}.{symbol} existe encore — "
            f"la migration LANG-MIGRATION-001 est incomplète."
        )


# ── TestNoFrenchCallsRemain ────────────────────────────────────────────────────

_FRENCH_PATTERNS = [
    "creer_session",
    "supprimer_session",
    "regenerer_session",
    "authentifier_session",
    "est_authentifie",
    "get_utilisateur",
    "utilisateur_a_role",
    "DUREE_SESSION",
    "verifier_mot_de_passe",
    "enregistrer_tentative",
    "MAX_TENTATIVES",
    "FENETRE_SECONDES",
    "est_limite_upload",
    "enregistrer_upload",
    "UPLOAD_FENETRE_SECONDES",
    r"\best_limite\b",
]


@pytest.mark.parametrize("pattern", _FRENCH_PATTERNS)
class TestNoFrenchCallsRemain:
    """Aucun fichier Python du projet (hors ce fichier) n'utilise les anciens noms."""

    def test_pattern_absent(self, pattern):
        result = subprocess.run(
            [
                "grep", "-rn", "--include=*.py",
                "--exclude=test_lang_migration_001.py",
                "--exclude=test_getting_started_3_0_001.py",
                "-E", pattern,
                "core/", "mvc/", "forge_cli/", "tests/", "integrations/",
            ],
            capture_output=True,
            text=True,
        )
        hits = [
            line for line in result.stdout.splitlines()
            if "__pycache__" not in line
        ]
        assert not hits, (
            f"Pattern '{pattern}' encore présent dans :\n" + "\n".join(hits)
        )


# ── TestUtilisateurIdParameter ────────────────────────────────────────────────

class TestUtilisateurIdParameter:
    """Le paramètre utilisateur_id a été renommé user_id dans update_password_hash."""

    def test_user_id_param_present(self):
        from mvc.models.auth_model import update_password_hash
        sig = inspect.signature(update_password_hash)
        assert "user_id" in sig.parameters

    def test_utilisateur_id_param_absent(self):
        from mvc.models.auth_model import update_password_hash
        sig = inspect.signature(update_password_hash)
        assert "utilisateur_id" not in sig.parameters
