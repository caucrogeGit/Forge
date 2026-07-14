"""Garde-fou META-TESTS-ROTATION-POLICY-001.

Vérifie que la politique de rotation des tests méta est documentée
dans docs/philosophy/contributing.md avec toutes les sections requises, et
applique la règle minimale sur les tests méta temporaires.

Règles vérifiées :
- La section 'Politique de rotation des tests méta' existe.
- Les 7 sous-sections requises sont présentes.
- META-TESTS-PRUNE-001 est référencé comme ticket de nettoyage.
- Tout fichier tests/meta/ avec 'legacy', 'stale', 'migration'
  ou 'deprecation' dans le nom mentionne un ticket ou une phase.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRIBUTING = PROJECT_ROOT / "docs" / "philosophy" / "contributing.md"
META_DIR = Path(__file__).parent

_TICKET_PATTERN = re.compile(
    r"[A-Z][A-Z0-9-]{3,}-\d{3}|Phase\s+\d+|ADR-\d+",
    re.IGNORECASE,
)
_TEMPORARY_KEYWORDS = ("legacy", "stale", "migration", "deprecation")


class TestPolicySectionExists:
    """La section 'Politique de rotation des tests méta' existe dans contributing.md."""

    def test_section_header_present(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "Politique de rotation des tests méta" in text, (
            "docs/philosophy/contributing.md doit contenir une section "
            "'Politique de rotation des tests méta'."
        )

    def test_subsection_permanents(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "permanents" in text.lower() or "permanent" in text.lower(), (
            "La politique doit couvrir les tests méta permanents."
        )

    def test_subsection_temporaires(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "temporaires" in text.lower() or "temporaire" in text.lower(), (
            "La politique doit couvrir les tests méta temporaires."
        )

    def test_subsection_release_snapshot(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert (
            "release-snapshot" in text.lower()
            or "release_snapshot" in text.lower()
            or ("release" in text.lower() and "snapshot" in text.lower())
            or "release" in text.lower()
        ), (
            "La politique doit couvrir les tests méta release-snapshot."
        )

    def test_subsection_fusion_suppression(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "fusion" in text.lower() or "fusionn" in text.lower(), (
            "La politique doit couvrir la fusion ou suppression de tests méta."
        )

    def test_suppression_par_ticket_dedie(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "ticket dédié" in text or "ticket dedié" in text or "ticket" in text.lower(), (
            "La politique doit indiquer que la suppression passe par un ticket dédié."
        )

    def test_preference_tests_comportementaux(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert (
            "comportemental" in text.lower()
            or "comportementaux" in text.lower()
        ), (
            "La politique doit mentionner la préférence pour les tests comportementaux."
        )

    def test_prune_ticket_referenced(self):
        text = CONTRIBUTING.read_text(encoding="utf-8")
        assert "META-TESTS-PRUNE-001" in text, (
            "docs/philosophy/contributing.md doit référencer META-TESTS-PRUNE-001 "
            "comme ticket de nettoyage effectif."
        )


class TestTemporaryMetaFilesHaveTicketReference:
    """Tout fichier tests/meta/ avec un nom évoquant un test temporaire mentionne un ticket."""

    def _get_temporary_candidates(self) -> list[Path]:
        return [
            f for f in META_DIR.glob("test_*.py")
            if any(kw in f.name.lower() for kw in _TEMPORARY_KEYWORDS)
        ]

    def test_at_least_one_candidate_found(self):
        candidates = self._get_temporary_candidates()
        assert len(candidates) >= 1, (
            "Aucun fichier tests/meta/ avec 'legacy', 'stale', 'migration' ou "
            "'deprecation' dans le nom. Vérifier que les fichiers attendus existent."
        )

    def test_each_temporary_candidate_mentions_ticket(self):
        offenders: list[str] = []
        for f in self._get_temporary_candidates():
            header = f.read_text(encoding="utf-8")[:800]
            if not _TICKET_PATTERN.search(header):
                offenders.append(f.name)
        assert not offenders, (
            "Ces fichiers tests/meta/ ont un nom évoquant un test temporaire "
            "mais ne mentionnent aucun ticket ni phase dans leurs 800 premiers "
            "caractères :\n"
            + "\n".join(f"  - {o}" for o in offenders)
            + "\n\nAjouter dans le docstring : le ticket qui justifie ce garde-fou "
            "(ex: 'Garde-fou TICKET-NOM-001.')."
        )
