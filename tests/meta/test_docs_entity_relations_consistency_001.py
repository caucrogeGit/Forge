"""Garde-fou DOCS-ENTITY-RELATIONS-CONSISTENCY-001.

Vérifie que les 3 documents de référence sur les relations entre entités
disent la même chose sur many_to_many :
  - docs/entity_architecture.md
  - docs/reference/api.md
  - docs/relations.md

Historiquement, entity_architecture.md affirmait « Forge V1 ne fournit pas
de many_to_many direct » alors que reference/api.md et relations.md le
documentaient comme supporté. Contradiction résolue par C4.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

ENTITY_ARCH = PROJECT_ROOT / "docs" / "entity_architecture.md"
API_REF = PROJECT_ROOT / "docs" / "reference" / "api.md"
RELATIONS_MD = PROJECT_ROOT / "docs" / "relations.md"


class TestManyToManyConsistency:
    """Les 3 fichiers s'accordent sur le support de many_to_many."""

    @pytest.mark.parametrize("path", [ENTITY_ARCH, API_REF, RELATIONS_MD],
                             ids=["entity_architecture", "api_ref", "relations"])
    def test_files_exist(self, path: Path):
        assert path.exists(), f"{path.relative_to(PROJECT_ROOT)} doit exister"

    def test_entity_arch_no_longer_denies_many_to_many(self):
        """entity_architecture.md ne dit plus que many_to_many n'est pas supporté."""
        text = ENTITY_ARCH.read_text(encoding="utf-8")
        assert "ne fournit pas" not in text.lower() or "many_to_many" not in text, (
            "docs/entity_architecture.md ne doit plus contenir une phrase niant "
            "le support de many_to_many — ce type est supporté dans relations.json."
        )
        # Forme exacte de l'ancienne contradiction
        assert "ne fournit pas de `many_to_many`" not in text, (
            "La phrase 'ne fournit pas de `many_to_many`' ne doit plus apparaître "
            "dans entity_architecture.md."
        )

    def test_entity_arch_not_in_unsupported_list(self):
        """`many_to_many` ne figure plus dans la liste 'Hors V1' de entity_architecture.md."""
        text = ENTITY_ARCH.read_text(encoding="utf-8")
        lines = text.splitlines()
        in_hors_section = False
        for line in lines:
            if line.strip().startswith("### Hors"):
                in_hors_section = True
            elif line.startswith("### ") or line.startswith("## "):
                in_hors_section = False
            if in_hors_section and "many_to_many" in line:
                assert False, (
                    "La section 'Hors V1' de entity_architecture.md ne doit pas "
                    "lister `many_to_many` — ce type est supporté."
                )

    def test_entity_arch_says_many_to_many_supported(self):
        """entity_architecture.md affirme que many_to_many est supporté."""
        text = ENTITY_ARCH.read_text(encoding="utf-8")
        assert "many_to_many" in text, (
            "docs/entity_architecture.md doit mentionner many_to_many."
        )
        assert "supporté" in text, (
            "docs/entity_architecture.md doit indiquer que many_to_many est supporté."
        )

    def test_api_ref_says_many_to_many_supported(self):
        """reference/api.md confirme le support de many_to_many."""
        text = API_REF.read_text(encoding="utf-8")
        assert "many_to_many" in text, (
            "docs/reference/api.md doit mentionner many_to_many."
        )

    def test_relations_md_says_many_to_many_supported(self):
        """relations.md confirme le support de many_to_many."""
        text = RELATIONS_MD.read_text(encoding="utf-8")
        assert "many_to_many" in text, (
            "docs/relations.md doit mentionner many_to_many."
        )
        assert "supporté" in text, (
            "docs/relations.md doit indiquer que many_to_many est supporté."
        )
