"""Garde-fou OPTIN-PYPI-NAMES-CHECK-001.

Verifie que :
- le rapport d'audit existe dans docs/history/audits/ ;
- OPTIN-PYPI-NAMES-CHECK-001 est mentionne dans le rapport ;
- les 5 noms opt-in sont listes dans le rapport ;
- le rapport contient PyPI et TestPyPI ;
- forge-mvc-mfa est marque non publiable (NE_PAS_PUBLIER) ;
- forge-mvc-media est marque non publiable ;
- aucune commande twine upload n'est recommandee dans ce rapport ;
- la roadmap marque OPTIN-PYPI-NAMES-CHECK-001 livre.

Ce test ne fait aucune verification reseau.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

AUDIT_REPORT = PROJECT_ROOT / "docs" / "history" / "audits" / "optin-pypi-names-check-001.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"

_OPTIN_NAMES = [
    "forge-mvc-rbac",
    "forge-mvc-workflow",
    "forge-mvc-stats",
    "forge-mvc-media",
    "forge-mvc-mfa",
]


class TestRoadmapReference:
    def test_roadmap_mentions_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "OPTIN-PYPI-NAMES-CHECK-001" in text, (
            "La roadmap doit mentionner OPTIN-PYPI-NAMES-CHECK-001."
        )

    def test_roadmap_marks_ticket_as_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        idx = text.find("OPTIN-PYPI-NAMES-CHECK-001")
        assert idx != -1
        bloc = text[idx:idx + 120]
        assert "livré" in bloc, (
            "OPTIN-PYPI-NAMES-CHECK-001 doit etre marque 'livré' dans la roadmap."
        )


class TestAuditReportExists:
    def test_rapport_exists(self):
        assert AUDIT_REPORT.exists(), (
            f"{AUDIT_REPORT} doit exister — rapport d'audit OPTIN-PYPI-NAMES-CHECK-001."
        )

    def test_rapport_mentions_ticket(self):
        text = AUDIT_REPORT.read_text(encoding="utf-8")
        assert "OPTIN-PYPI-NAMES-CHECK-001" in text, (
            "Le rapport doit mentionner OPTIN-PYPI-NAMES-CHECK-001."
        )


class TestAuditReportContent:
    def _text(self) -> str:
        return AUDIT_REPORT.read_text(encoding="utf-8")

    @pytest.mark.parametrize("pkg_name", _OPTIN_NAMES)
    def test_rapport_liste_tous_les_noms(self, pkg_name):
        assert pkg_name in self._text(), (
            f"Le rapport doit lister le package {pkg_name!r}."
        )

    def test_rapport_mentionne_pypi(self):
        assert "PyPI" in self._text(), (
            "Le rapport doit mentionner PyPI."
        )

    def test_rapport_mentionne_testpypi(self):
        text = self._text()
        assert "TestPyPI" in text or "test.pypi" in text, (
            "Le rapport doit mentionner TestPyPI."
        )

    def test_mfa_marque_ne_pas_publier(self):
        text = self._text()
        assert "forge-mvc-mfa" in text, "Le rapport doit lister forge-mvc-mfa."
        assert (
            "NE_PAS_PUBLIER" in text
            or "ne pas publier" in text.lower()
            or "non publiable" in text.lower()
        ), (
            "Le rapport doit indiquer que forge-mvc-mfa ne doit pas etre publie."
        )

    def test_media_marque_ne_pas_publier(self):
        text = self._text()
        assert "forge-mvc-media" in text, "Le rapport doit lister forge-mvc-media."
        assert (
            "NE_PAS_PUBLIER" in text
            or "ne pas publier" in text.lower()
            or "non publiable" in text.lower()
        ), (
            "Le rapport doit indiquer que forge-mvc-media ne doit pas etre publie."
        )

    def test_rapport_pas_de_twine_upload(self):
        text = self._text()
        assert "twine upload dist/" not in text, (
            "Le rapport ne doit pas recommander 'twine upload dist/' (audit seulement)."
        )
