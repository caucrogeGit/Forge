"""Garde-fou TESTS-BEHAVIOR-FIRST-001.

Vérifie que docs/contributing.md documente la règle behavior-first :
- la notion de "behavior-first" est présente ;
- la distinction test comportemental / test méta est expliquée ;
- la condition "quand un comportement peut être exécuté" est mentionnée ;
- la règle que les tests méta ne remplacent pas les tests comportementaux
  est explicite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRIBUTING = PROJECT_ROOT / "docs" / "contributing.md"


@pytest.fixture(scope="module")
def contributing() -> str:
    assert CONTRIBUTING.exists(), f"docs/contributing.md introuvable : {CONTRIBUTING}"
    return CONTRIBUTING.read_text(encoding="utf-8")


class TestBehaviorFirstRuleDocumented:
    """La règle behavior-first est documentée dans docs/contributing.md."""

    def test_behavior_first_mention(self, contributing):
        assert "behavior-first" in contributing.lower() or "behavior first" in contributing.lower(), (
            "docs/contributing.md doit mentionner la règle 'behavior-first'."
        )

    def test_test_comportemental_mention(self, contributing):
        lower = contributing.lower()
        assert "test comportemental" in lower or "tests comportementaux" in lower, (
            "docs/contributing.md doit mentionner les tests comportementaux."
        )

    def test_test_meta_mention(self, contributing):
        lower = contributing.lower()
        assert "test méta" in lower or "tests méta" in lower, (
            "docs/contributing.md doit mentionner les tests méta."
        )

    def test_executability_condition_present(self, contributing):
        lower = contributing.lower()
        assert (
            "peut être exécuté" in lower
            or "peut être exécutée" in lower
            or "quand forge expose" in lower
            or "quand un comportement" in lower
        ), (
            "docs/contributing.md doit préciser la condition d'application de la règle "
            "(quand un comportement peut être exécuté)."
        )

    def test_meta_does_not_replace_behavioral(self, contributing):
        lower = contributing.lower()
        assert (
            "ne doit pas être la seule preuve" in lower
            or "ne remplace pas" in lower
            or "ne remplacent pas" in lower
            or "compléter" in lower
        ), (
            "docs/contributing.md doit indiquer que les tests méta ne remplacent pas "
            "les tests comportementaux."
        )

    def test_section_header_present(self, contributing):
        assert "Règle behavior-first" in contributing, (
            "docs/contributing.md doit contenir une section 'Règle behavior-first'."
        )
