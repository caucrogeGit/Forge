"""Garde-fou ROADMAP-3.0.1-3.0.2-001.

Vérifie que la roadmap reflète les états Phase G (3.0.1) et
Scénario C (3.0.2).

Origine : audit F2/F3 — compteur tests obsolète (9279 vs ~9501),
aucune section pour Phase G ni Scénario C.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


class TestRoadmapStructure:
    """La roadmap a la structure attendue post-Scénario-C."""

    def test_roadmap_exists(self):
        assert ROADMAP.exists()

    def test_no_obsolete_test_count(self):
        """La roadmap ne mentionne plus le compteur 9279."""
        text = ROADMAP.read_text(encoding="utf-8")
        assert "9279 passed" not in text and "9279 passants" not in text, (
            "La roadmap mentionne encore '9279 passed' (compteur obsolète). "
            "La suite est à ~9501 passants à la fin du Scénario C."
        )

    def test_state_actual_section(self):
        """La section 'État actuel — Forge X.Y.Z' existe."""
        text = ROADMAP.read_text(encoding="utf-8")
        assert re.search(r"État actuel — Forge \d", text), (
            "Section 'État actuel — Forge X.Y.Z' attendue."
        )


class TestPostThreeZeroSectionExists:
    """La section 'Historique de consolidation post-3.0' existe."""

    def test_section_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "## Historique de consolidation post-3.0" in text, (
            "Section 'Historique de consolidation post-3.0' doit être ajoutée "
            "(sur le modèle de la section 'post-2.0' déjà présente)."
        )

    @pytest.mark.parametrize("ticket_code", [
        "G1 SESSIONS-LANG-ALIGN-001",
        "G8 CLI-AUTH-INIT-OIDC-SQL-001",
        "PR1 DOCS-CLI-COMMANDS-REFERENCE-001",
        "PR4 LANDING-POSITIONNEMENT-VISIBILITY-001",
        "RELEASE-3.0.1-PATCH-STABLE-001",
    ])
    def test_phase_g_ticket_mentioned(self, ticket_code: str):
        """Les tickets Phase G + pré-release sont mentionnés."""
        text = ROADMAP.read_text(encoding="utf-8")
        match = re.search(
            r"## Historique de consolidation post-3\.0.*?(?=\n## )",
            text, re.DOTALL,
        )
        assert match, "Section 'Historique de consolidation post-3.0' introuvable"
        section = match.group(0)
        assert ticket_code in section, (
            f"Ticket Phase G/PR '{ticket_code}' non mentionné dans la "
            f"section Historique post-3.0."
        )


class TestScenarioCSectionExists:
    """La section 'Scénario C — Consolidation 3.0.2' existe."""

    def test_section_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "## Scénario C — Consolidation 3.0.2" in text, (
            "Section 'Scénario C — Consolidation 3.0.2' doit être ajoutée."
        )

    @pytest.mark.parametrize("ticket_code", [
        "T1 PYTEST-REPRODUCIBLE-001",
        "T2b PACKAGING-WHEEL-CONTENT-001",
        "T14 CORE-RBAC-PLUGIN-MECHANISM-001",
        "T7 DOCS-3.0.1-VERSION-SWEEP-001",
        "T9 CLAUDE-MD-3.0.2-REFRESH-001",
        "T5 CHANGELOG-3.0.1-3.0.2-001",
        "T22 RELEASE-3.0.2-PATCH-STABLE-001",
    ])
    def test_scenario_c_ticket_mentioned(self, ticket_code: str):
        """Les tickets clés du Scénario C sont mentionnés."""
        text = ROADMAP.read_text(encoding="utf-8")
        match = re.search(
            r"## Scénario C — Consolidation 3\.0\.2.*?(?=\n## )",
            text, re.DOTALL,
        )
        assert match, "Section 'Scénario C' introuvable"
        section = match.group(0)
        assert ticket_code in section, (
            f"Ticket Scénario C '{ticket_code}' non mentionné."
        )

    def test_t18_documented_as_merged(self):
        """T18 (CI-COMMENTS-CLEANUP-001) est documenté comme intégré dans T2b."""
        text = ROADMAP.read_text(encoding="utf-8")
        match = re.search(
            r"## Scénario C — Consolidation 3\.0\.2.*?(?=\n## )",
            text, re.DOTALL,
        )
        if match:
            section = match.group(0)
            if "T18 " in section:
                assert "intégré" in section or "fusionné" in section.lower(), (
                    "Si T18 apparaît dans la section Scénario C, "
                    "il doit être marqué comme intégré dans T2b."
                )


class TestNoForwardLooking:
    """La roadmap ne contient pas de promesses obsolètes."""

    def test_no_obsolete_forge_3_0_in_progress(self):
        """Pas de phrases actives décrivant Forge 3.0 comme 'en cours'."""
        text = ROADMAP.read_text(encoding="utf-8")
        forbidden_patterns = [
            "Forge 3.0 en cours",
            "refonte 3.0 en cours",
            "v3.0 en préparation",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in text, (
                f"Roadmap contient '{pattern}' alors que v3.0 et v3.0.1 sont taggés."
            )
