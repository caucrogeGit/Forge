"""Garde-fou PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001.

Vérifie que CHARTE_DOC.md section 7 documente bien les trois
environnements (A. Runtime core-only, B. Test core-only, C. Test
complet) avec leurs prérequis et promesses.

Ne vérifie pas le contenu fonctionnel (déjà couvert par d'autres
tests) mais la présence et la cohérence du contrat documenté.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
CHARTE = PROJECT_ROOT / "CHARTE_DOC.md"


def _section_7() -> str:
    """Retourne le contenu de la section 7 de la charte."""
    text = CHARTE.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s+7\.\s", re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return ""
    start = match.start()
    next_section = re.search(r"^##\s+8\.\s", text[start + 1:], re.MULTILINE)
    if next_section:
        end = start + 1 + next_section.start()
        return text[start:end]
    return text[start:]


def test_section_7_exists():
    section = _section_7()
    assert section, "Section 7 (Règles Git et release) introuvable dans CHARTE_DOC.md"


def test_three_environments_documented():
    """La charte section 7 doit nommer les 3 environnements."""
    section = _section_7()
    required_markers = [
        "Runtime core-only",
        "Test core-only",
        "Test complet",
    ]
    missing = [m for m in required_markers if m not in section]
    if missing:
        raise AssertionError(
            f"CHARTE_DOC.md section 7 ne documente pas les environnements : "
            f"{missing}. Voir PYTEST-CORE-ONLY-CONTRACT-CLARIFY-001."
        )


def test_validation_commands_listed():
    """Les 5 commandes de validation sont nommées dans la section 7."""
    section = _section_7()
    required_commands = [
        "pytest",
        "compileall",
        "ruff check",
        "mkdocs build --strict",
        "git diff --check",
    ]
    missing = [c for c in required_commands if c not in section]
    if missing:
        raise AssertionError(
            f"CHARTE_DOC.md section 7 ne liste pas les commandes : {missing}"
        )
