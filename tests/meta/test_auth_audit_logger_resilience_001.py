"""Garde-fou AUTH-AUDIT-LOGGER-RESILIENCE-001.

Verifie que :
- AUTH-AUDIT-LOGGER-RESILIENCE-001 est reference dans la roadmap ;
- core/auth/audit.py ne contient pas d'import forge_mvc_mfa ;
- core/auth/audit.py ne contient pas d'import forge_mvc_rbac ;
- core/auth/audit.py ne contient pas d'import pyotp ;
- la documentation mentionne que l'audit auth est best-effort ou non bloquant ;
- la documentation mentionne que l'echec du logger ne doit pas casser le flux auth.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

AUDIT_PY = PROJECT_ROOT / "core" / "auth" / "audit.py"
AUTH_DOC = PROJECT_ROOT / "docs" / "auth.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


class TestRoadmapReference:
    def test_roadmap_mentions_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "AUTH-AUDIT-LOGGER-RESILIENCE-001" in text, (
            "La roadmap doit mentionner AUTH-AUDIT-LOGGER-RESILIENCE-001."
        )

    def test_roadmap_marks_ticket_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("AUTH-AUDIT-LOGGER-RESILIENCE-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "AUTH-AUDIT-LOGGER-RESILIENCE-001 doit etre marque 'livré' dans la roadmap."
        )


class TestNoOptInImportsInCoreAudit:
    def _src(self) -> str:
        return AUDIT_PY.read_text(encoding="utf-8")

    def test_no_forge_mvc_mfa(self):
        assert "forge_mvc_mfa" not in self._src(), (
            "core/auth/audit.py ne doit pas importer forge_mvc_mfa."
        )

    def test_no_forge_mvc_rbac(self):
        assert "forge_mvc_rbac" not in self._src(), (
            "core/auth/audit.py ne doit pas importer forge_mvc_rbac."
        )

    def test_no_pyotp(self):
        assert "pyotp" not in self._src(), (
            "core/auth/audit.py ne doit pas importer pyotp."
        )


class TestDocumentationResilience:
    def _doc(self) -> str:
        return AUTH_DOC.read_text(encoding="utf-8")

    def test_doc_mentions_best_effort_or_non_bloquant(self):
        text = self._doc()
        assert "best-effort" in text or "non bloquant" in text, (
            "docs/auth.md doit mentionner que l'audit est best-effort ou non bloquant."
        )

    def test_doc_mentions_failure_does_not_break_flow(self):
        text = self._doc()
        assert (
            "ne doit jamais etre bloquee" in text
            or "ne casse pas" in text
            or "ne bloque pas" in text
            or "ne doit pas casser" in text
        ), (
            "docs/auth.md doit mentionner que l'echec du logger ne casse pas le flux auth."
        )
