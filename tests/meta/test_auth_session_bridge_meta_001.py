"""Garde-fou documentaire AUTH-SESSION-COMPATIBILITY-BRIDGE-001.

Vérifie que :
- core/auth/session.py contient le pont de compatibilité legacy→canonique ;
- core/security/session.py contient le pont de compatibilité canonique→legacy ;
- aucune importation circulaire n'a été introduite (pas d'import core.auth dans core.security) ;
- le commentaire d'identification du pont est présent dans chaque fichier.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

AUTH_SESSION = PROJECT_ROOT / "core" / "auth" / "session.py"
SECURITY_SESSION = PROJECT_ROOT / "core" / "security" / "session.py"


def _auth_text() -> str:
    if not AUTH_SESSION.exists():
        pytest.skip("core/auth/session.py introuvable")
    return AUTH_SESSION.read_text(encoding="utf-8")


def _security_text() -> str:
    if not SECURITY_SESSION.exists():
        pytest.skip("core/security/session.py introuvable")
    return SECURITY_SESSION.read_text(encoding="utf-8")


class TestCanonicalBridgeLegacy:
    """core/auth/session.py reconnaît les sessions legacy."""

    def test_bridge_comment_present(self):
        """Le commentaire 'Pont de compatibilité' est présent dans core/auth/session.py."""
        assert "Pont de compatibilité" in _auth_text(), (
            "core/auth/session.py doit contenir le commentaire de pont de compatibilité"
        )

    def test_session_key_authenticated_imported_in_bridge(self):
        """core/auth/session.py importe SESSION_KEY_AUTHENTICATED dans le pont."""
        assert "SESSION_KEY_AUTHENTICATED" in _auth_text(), (
            "core/auth/session.py doit référencer SESSION_KEY_AUTHENTICATED pour le pont legacy"
        )

    def test_no_top_level_circular_import(self):
        """core/auth/session.py n'importe pas core.security au niveau module (anti-circulaire)."""
        lines = _auth_text().splitlines()
        top_level_imports = [
            line for line in lines
            if line.startswith("from core.security") or line.startswith("import core.security")
        ]
        assert not top_level_imports, (
            "core/auth/session.py ne doit pas importer core.security au niveau module — "
            f"imports détectés : {top_level_imports}"
        )


class TestLegacyBridgeCanonical:
    """core/security/session.py reconnaît les sessions canoniques."""

    def test_bridge_comment_present(self):
        """Le commentaire 'Pont de compatibilité' est présent dans core/security/session.py."""
        assert "Pont de compatibilité" in _security_text(), (
            "core/security/session.py doit contenir le commentaire de pont de compatibilité"
        )

    def test_canonical_key_literal_present(self):
        """core/security/session.py référence la clé canonique _auth_user_id."""
        assert "_auth_user_id" in _security_text(), (
            "core/security/session.py doit référencer '_auth_user_id' pour le pont canonique"
        )

    def test_no_import_core_auth_session(self):
        """core/security/session.py n'importe pas core.auth.session (anti-circulaire)."""
        text = _security_text()
        assert "from core.auth.session" not in text and "import core.auth.session" not in text, (
            "core/security/session.py ne doit pas importer core.auth.session — "
            "utiliser la clé littérale '_auth_user_id' pour éviter les imports circulaires"
        )
