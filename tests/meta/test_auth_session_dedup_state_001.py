"""Garde-fou AUTH-SESSION-DEDUP-001 — état de déduplication.

Vérifie que :
- forge_mvc_mfa.mfa n'importe plus get_session depuis core.security.session
  (migré vers get_session_store().get() directement dans _resolve_mfa_session) ;
- forge_mvc_mfa.mfa importe toujours get_session_store depuis core.sessions.manager
  (pattern canonique confirmé) ;
- core/security/decorators.py continue d'importer depuis core.security.session
  (legacy conservé intentionnellement — équivalence avec login_required non établie).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

MFA_SOURCE = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "forge_mvc_mfa" / "mfa.py"
DECORATORS_SOURCE = PROJECT_ROOT / "core" / "security" / "decorators.py"


def _mfa_text() -> str:
    if not MFA_SOURCE.exists():
        pytest.skip("forge_mvc_mfa/mfa.py introuvable")
    return MFA_SOURCE.read_text(encoding="utf-8")


def _decorators_text() -> str:
    if not DECORATORS_SOURCE.exists():
        pytest.skip("core/security/decorators.py introuvable")
    return DECORATORS_SOURCE.read_text(encoding="utf-8")


class TestMfaSessionMigration:
    """forge_mvc_mfa/mfa.py utilise le store directement pour lire les sessions."""

    def test_mfa_does_not_import_get_session_from_core_security(self):
        """mfa.py ne doit plus importer get_session depuis core.security.session.

        Résultat de la migration AUTH-SESSION-DEDUP-001 : _resolve_mfa_session
        utilise désormais get_session_store().get(session_id) directement,
        comme _persist_session_changes le fait déjà.
        """
        text = _mfa_text()
        assert "from core.security.session import get_session," not in text, (
            "mfa.py importe encore get_session depuis core.security.session — "
            "migration AUTH-SESSION-DEDUP-001 attendue"
        )

    def test_mfa_imports_get_session_store_from_sessions_manager(self):
        """mfa.py importe get_session_store depuis core.sessions.manager."""
        assert "from core.sessions.manager import get_session_store" in _mfa_text(), (
            "mfa.py doit importer get_session_store depuis core.sessions.manager"
        )


class TestDecoratorsLegacyConserved:
    """core/security/decorators.py conserve intentionnellement ses imports legacy.

    Justification : require_auth vérifie SESSION_KEY_AUTHENTICATED + SESSION_KEY_USER
    (clés legacy) ; login_required vérifie _auth_user_id (canonique). Équivalence
    non établie — migration interdite sans changer la sémantique.
    Ticket 4.3 (AUTH-SESSION-LEGACY-DEPRECATION-001) ajoutera les warnings.
    """

    def test_decorators_still_imports_from_core_security_session(self):
        """decorators.py importe toujours depuis core.security.session (legacy conservé)."""
        assert "from core.security.session import" in _decorators_text(), (
            "decorators.py devrait encore importer depuis core.security.session "
            "(legacy conservé intentionnellement)"
        )
