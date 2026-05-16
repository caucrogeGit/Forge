"""Garde-fou AUTH-SESSION-CANONICAL-DECISION-001.

Vérifie que docs/adr/010-auth-session-canonical-api.md existe et contient
les éléments contractuels de la décision canonique auth/session :
- core.auth.session canonique
- core.security.session legacy
- absence de warning à l'import
- référence aux tickets de transition
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
ADR_010 = PROJECT_ROOT / "docs" / "adr" / "010-auth-session-canonical-api.md"


def _text() -> str:
    if not ADR_010.exists():
        pytest.skip("docs/adr/010-auth-session-canonical-api.md n'existe pas")
    return ADR_010.read_text(encoding="utf-8")


class TestAdr010Exists:
    """L'ADR-010 existe."""

    def test_adr_file_exists(self):
        assert ADR_010.exists(), (
            "docs/adr/010-auth-session-canonical-api.md doit exister"
        )


class TestAdr010MentionsCanonicalStack:
    """L'ADR mentionne core.auth.session comme API canonique."""

    def test_core_auth_session_mentioned(self):
        assert "core.auth.session" in _text(), (
            "ADR-010 doit mentionner core.auth.session"
        )

    def test_core_auth_session_declared_canonical(self):
        text = _text()
        assert "canonique" in text.lower() or "canonical" in text.lower(), (
            "ADR-010 doit déclarer une API canonique"
        )


class TestAdr010MentionsLegacyStack:
    """L'ADR mentionne core.security.session comme API legacy."""

    def test_core_security_session_mentioned(self):
        assert "core.security.session" in _text(), (
            "ADR-010 doit mentionner core.security.session"
        )

    def test_core_security_session_declared_legacy(self):
        text = _text()
        assert "legacy" in text.lower(), (
            "ADR-010 doit déclarer core.security.session comme legacy"
        )


class TestAdr010NoImportWarning:
    """L'ADR précise qu'il ne faut pas de warning à l'import."""

    def test_no_import_warning_rule(self):
        text = _text()
        assert "import" in text.lower() and (
            "DeprecationWarning" in text or "warning" in text.lower()
        ), (
            "ADR-010 doit mentionner la règle concernant les DeprecationWarning à l'import"
        )


class TestAdr010ReferencesTransitionTickets:
    """L'ADR référence les tickets de la transition."""

    def test_references_auth_session_dedup(self):
        assert "AUTH-SESSION-DEDUP-001" in _text(), (
            "ADR-010 doit référencer AUTH-SESSION-DEDUP-001"
        )

    def test_references_auth_session_legacy_deprecation(self):
        assert "AUTH-SESSION-LEGACY-DEPRECATION-001" in _text(), (
            "ADR-010 doit référencer AUTH-SESSION-LEGACY-DEPRECATION-001"
        )
