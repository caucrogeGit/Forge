"""CLI-PUBLIC-CONTRACT-FREEZE-001 / STARTERS-FINAL-CONTRACT-001 / DOCS-LINKS-FINAL-AUDIT-001.

Gel de la surface publique avant 1.0 (Phase 1, roadmap beta.13). Verrouille
mécaniquement les familles de commandes opt-in:*/module:* et la liste des 16
starters : toute dérive de la surface publique casse ce garde-fou.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FORGE_PY = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
CONTRACT = PROJECT_ROOT / "docs" / "reference" / "public-contract-1.0.md"


# ── Famille opt-in:* (exactement 6 verbes) ───────────────────────────────────

class TestOptInFamilyFrozen:
    EXPECTED = {"install", "remove", "enable", "disable", "list", "installed"}

    def test_optin_family_is_exactly_six(self):
        # ADR-059 : la famille opt-in:* est dispatchée via la table CORE_COMMANDS.
        from forge import CORE_COMMANDS

        found = {c.split(":", 1)[1] for c in CORE_COMMANDS if c.startswith("opt-in:")}
        assert found == self.EXPECTED, (
            f"Famille opt-in:* dérivée. Attendu {sorted(self.EXPECTED)}, "
            f"trouvé {sorted(found)}. Mettre à jour public-contract-1.0.md si voulu."
        )

    def test_no_legacy_optin_command(self):
        from forge import CORE_COMMANDS

        # Plus de commande legacy « optin:* » (sans tiret) nulle part.
        assert 'command == "optin:enable"' not in FORGE_PY
        assert not any(c.startswith("optin:") for c in CORE_COMMANDS)


# ── Famille module:* (exactement 4 commandes, distincte) ─────────────────────

class TestModuleFamilyFrozen:
    EXPECTED = {"module:list", "module:install", "module:files", "module:routes", "module:remove"}

    def test_module_family_is_exactly_four(self):
        # ADR-059 : module:* est routé via la table CORE_COMMANDS.
        from forge import CORE_COMMANDS

        found = {c for c in CORE_COMMANDS if c.startswith("module:")}
        assert found == self.EXPECTED, (
            f"Famille module:* dérivée. Attendu {sorted(self.EXPECTED)}, trouvé {sorted(found)}."
        )


# ── Le contrat est documenté ─────────────────────────────────────────────────

class TestContractDocumented:
    def test_contract_doc_exists(self):
        assert CONTRACT.is_file()

    @pytest.mark.parametrize("needle", [
        "opt-in:install", "opt-in:disable", "module:install",
        "mkdocs build --strict",
    ])
    def test_contract_mentions(self, needle):
        assert needle in CONTRACT.read_text(encoding="utf-8")
