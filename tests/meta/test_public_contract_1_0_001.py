"""CLI-PUBLIC-CONTRACT-FREEZE-001 / STARTERS-FINAL-CONTRACT-001 / DOCS-LINKS-FINAL-AUDIT-001.

Gel de la surface publique avant 1.0 (Phase 1, roadmap beta.13). Verrouille
mécaniquement les familles de commandes opt-in:*/module:* et la liste des 16
starters : toute dérive de la surface publique casse ce garde-fou.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
FORGE_PY = (PROJECT_ROOT / "forge.py").read_text(encoding="utf-8")
CONTRACT = PROJECT_ROOT / "docs" / "reference" / "public-contract-1.0.md"


# ── Famille opt-in:* (exactement 5 verbes) ───────────────────────────────────

class TestOptInFamilyFrozen:
    EXPECTED = {"install", "remove", "enable", "disable", "list"}

    def test_optin_family_is_exactly_five(self):
        found = set(re.findall(r'command == "opt-in:([a-z]+)"', FORGE_PY))
        assert found == self.EXPECTED, (
            f"Famille opt-in:* dérivée. Attendu {sorted(self.EXPECTED)}, "
            f"trouvé {sorted(found)}. Mettre à jour public-contract-1.0.md si voulu."
        )

    def test_no_legacy_optin_command(self):
        assert 'command == "optin:enable"' not in FORGE_PY
        assert 'command == "optin:list"' not in FORGE_PY


# ── Famille module:* (exactement 4 commandes, distincte) ─────────────────────

class TestModuleFamilyFrozen:
    EXPECTED = {"module:list", "module:install", "module:files", "module:routes", "module:remove"}

    def test_module_family_is_exactly_four(self):
        # module:* est routé via un `command in (...)` tuple
        m = re.search(r'command in \(([^)]*module:[^)]*)\)', FORGE_PY)
        assert m, "Le routage tuple de module:* est introuvable dans forge.py"
        found = set(re.findall(r'"(module:[a-z]+)"', m.group(1)))
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
