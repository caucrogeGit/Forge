"""Garde-fou MEDIA-CORE-BOUNDARY-AUDIT-001.

Vérifie que le rapport d'audit de la frontière core média / module opt-in
existe, est structuré correctement, et ne prétend pas avoir déplacé du code.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT_FILE = PROJECT_ROOT / "docs" / "history" / "audits" / "media-core-boundary-audit-001.md"


def _text() -> str:
    return AUDIT_FILE.read_text(encoding="utf-8")


class TestAuditFileExists:

    def test_audit_file_exists(self):
        assert AUDIT_FILE.exists(), (
            "docs/history/audits/media-core-boundary-audit-001.md doit exister."
        )

    def test_audit_mentions_ticket(self):
        assert "MEDIA-CORE-BOUNDARY-AUDIT-001" in _text()

    def test_audit_mentions_forge_mvc_media(self):
        assert "forge-mvc-media" in _text()

    def test_audit_mentions_packages_path(self):
        assert "packages/forge-mvc-media" in _text()


class TestAuditStructure:

    @pytest.mark.parametrize("section", [
        "## Objectif",
        "## Méthode",
        "## Synthèse",
        "## Carte actuelle du média",
        "## Éléments à conserver dans le core",
        "## Éléments à extraire vers forge-mvc-media",
        "## Usages dans les générateurs",
        "## Usages dans les starters",
        "## Usages dans les tests",
        "## Documentation concernée",
        "## Risques d'extraction",
        "## Décisions proposées",
        "## Tickets futurs suggérés",
        "## Conclusion",
    ])
    def test_section_present(self, section):
        assert section in _text(), f"Section '{section}' absente du rapport d'audit."


class TestAuditContent:

    def test_distinguishes_core_and_optin(self):
        text = _text()
        assert "CORE_GÉNÉRIQUE" in text
        assert "OPTIN_MEDIA" in text

    def test_mentions_core_elements_to_keep(self):
        text = _text()
        assert "storage.py" in text
        assert "validators.py" in text
        assert "manager.py" in text
        assert "image.py" in text
        assert "rate_limit.py" in text
        assert "exceptions.py" in text

    def test_mentions_elements_to_extract(self):
        text = _text()
        assert "media_repository.py" in text
        assert "media_gallery.py" in text

    def test_mentions_extraction_risks(self):
        text = _text()
        assert "controller_builder.py" in text or "générateurs" in text.lower()

    def test_does_not_claim_code_moved(self):
        text = _text()
        forbidden = [
            "a été déplacé",
            "ont été déplacés",
            "code déplacé",
            "migration effectuée",
        ]
        for phrase in forbidden:
            assert phrase not in text, (
                f"Le rapport d'audit ne doit pas prétendre avoir déplacé du code : "
                f"'{phrase}' trouvé."
            )

    def test_does_not_claim_optin_published(self):
        text = _text()
        assert "forge-mvc-media publié" not in text
        assert "paquet publié" not in text
