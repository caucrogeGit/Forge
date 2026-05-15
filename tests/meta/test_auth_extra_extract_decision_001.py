"""Garde-fou AUTH-EXTRA-EXTRACT-001.

Vérifie que la décision G2 sur le périmètre de core/auth/ est respectée :
les sous-modules rate_limit, audit et reset restent dans core (option C).

Décision documentée dans docs/adr/004-core-perimeter.md (section
"Décision complémentaire — Périmètre de core/auth/ résiduel").

Rationale : rate_limit est importé par core/security/hashing.py (dépendance
d'une primitive core sur un opt-in impossible) ; audit est consommé par
forge-mvc-mfa (opt-in ne doit pas dépendre d'un autre opt-in).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


class TestAuthSubmodulesInCore:
    """Les trois sous-modules core/auth/ restent dans le core (option C)."""

    def test_rate_limit_in_core(self):
        assert Path("core/auth/rate_limit.py").exists(), (
            "core/auth/rate_limit.py doit rester dans le core — "
            "il est importé par core/security/hashing.py."
        )

    def test_audit_in_core(self):
        assert Path("core/auth/audit.py").exists(), (
            "core/auth/audit.py doit rester dans le core — "
            "il est consommé par forge-mvc-mfa via lazy imports."
        )

    def test_reset_in_core(self):
        assert Path("core/auth/reset.py").exists(), (
            "core/auth/reset.py doit rester dans le core — "
            "spécifique Auth/User, aucune généricité externe."
        )

    def test_no_forge_mvc_auth_extra_package(self):
        """Aucun package opt-in forge-mvc-auth-extra n'existe (décision G2)."""
        assert not Path("packages/forge-mvc-auth-extra").exists(), (
            "packages/forge-mvc-auth-extra existe — si la décision G2 a été "
            "inversée, mettre à jour docs/adr/004-core-perimeter.md et ce test."
        )


class TestDecisionDocumented:
    """La décision G2 est documentée dans ADR-004."""

    def test_adr_004_mentions_rate_limit_decision(self):
        text = Path("docs/adr/004-core-perimeter.md").read_text(encoding="utf-8")
        assert "rate_limit" in text, (
            "ADR-004 doit mentionner la décision sur rate_limit "
            "(section AUTH-EXTRA-EXTRACT-001)."
        )

    def test_adr_004_mentions_auth_extra_extract(self):
        text = Path("docs/adr/004-core-perimeter.md").read_text(encoding="utf-8")
        assert "AUTH-EXTRA-EXTRACT-001" in text, (
            "ADR-004 doit référencer le ticket AUTH-EXTRA-EXTRACT-001."
        )

    def test_adr_004_documents_non_extraction_rationale(self):
        text = Path("docs/adr/004-core-perimeter.md").read_text(encoding="utf-8")
        assert "forge-mvc-auth-extra" in text, (
            "ADR-004 doit nommer forge-mvc-auth-extra dans les alternatives "
            "considérées et abandonnées."
        )
