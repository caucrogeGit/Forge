"""Garde-fou DOCS-API-REFERENCE-MODULES-001.

Vérifie que docs/reference/api.md mentionne les 4 modules officiels opt-in :
- forge-mvc-mfa
- forge-mvc-rbac
- forge-mvc-workflow
- forge-mvc-stats

Et qu'il lie vers leur page de référence détaillée.

Sans ce garde-fou, un utilisateur qui consulte api.md comme point d'entrée
de la doc de référence peut croire que ces modules n'existent pas (faux
négatif d'API, violation du principe 10 — contrat de complétude).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

API_REF = PROJECT_ROOT / "docs" / "reference" / "api.md"

# Cibles de lien dans api.md. Les opt-ins à doc embarquée (ADR-038) sont liés
# vers leur page montée sous /<slug>/reference/ ; les autres restent dans
# docs/reference/.
EXPECTED_MODULES = {
    "forge-mvc-mfa":      "mfa/reference.md",
    "forge-mvc-rbac":     "rbac/reference.md",
    "forge-mvc-workflow": "workflow/reference.md",
    "forge-mvc-stats":    "stats/reference.md",
}

_SECTION_PATTERNS = [
    r"##\s+Opt-ins officiels",  # vocabulaire canonique (OPTIN-VOCAB-001, ADR-016)
    r"##\s+Modules officiels",
    r"##\s+Modules opt-in",
    r"##\s+Optional modules",
]


class TestApiReferenceMentionsAllOptInModules:
    """docs/reference/api.md mentionne les 4 modules opt-in."""

    def test_file_exists(self):
        assert API_REF.exists()

    def test_all_modules_mentioned(self):
        """Les 4 noms de packages PyPI apparaissent dans api.md."""
        text = API_REF.read_text(encoding="utf-8")
        missing = [pkg for pkg in EXPECTED_MODULES if pkg not in text]
        assert not missing, (
            f"docs/reference/api.md ne mentionne pas les packages : {missing}. "
            f"Ajouter une section 'Modules officiels (opt-in)' qui les liste."
        )

    def test_section_modules_opt_in_present(self):
        """Une section dédiée 'Modules officiels' existe."""
        text = API_REF.read_text(encoding="utf-8")
        found = any(re.search(p, text, re.IGNORECASE) for p in _SECTION_PATTERNS)
        assert found, (
            "docs/reference/api.md doit contenir une section dédiée aux modules "
            "opt-in (titre `## Modules officiels (opt-in)` ou équivalent)."
        )


class TestApiReferenceLinksToModuleDocs:
    """Chaque module est lié vers sa page de référence."""

    def test_each_module_has_link_to_its_doc(self):
        text = API_REF.read_text(encoding="utf-8")
        for pkg, ref_page in EXPECTED_MODULES.items():
            pat = re.compile(rf"\]\([^)]*{re.escape(ref_page)}[^)]*\)")
            assert pat.search(text), (
                f"docs/reference/api.md ne contient pas de lien vers `{ref_page}` "
                f"pour le module {pkg}."
            )


class TestApiReferenceNoActivePipExtras:
    """Aucune commande active pip install forge-mvc[X] n'apparaît dans api.md.

    Contrat post-DOCS-OPTIN-INSTALL-CONTRACT-001 + DOCS-VERSION-SWEEP-BETA9-001 :
    les opt-ins `rbac`/`workflow`/`stats` ont été publiés en `1.0.0-beta.5`. La
    note documentaire est désormais rétrospective (« Disponible sur PyPI
    depuis … ») plutôt que prospective. Les commandes copiables restent
    interdites pour éviter qu'un copier-coller pré-publication soit possible
    avant qu'une vague PyPI ne soit effective.
    """

    def test_no_active_pip_install_extra(self):
        text = API_REF.read_text(encoding="utf-8")
        pat = re.compile(r"pip\s+install\s+forge-mvc\[\w+\]")
        matches = pat.findall(text)
        assert len(matches) == 0, (
            f"docs/reference/api.md ne doit contenir aucune commande copiable "
            f"`pip install forge-mvc[X]`. "
            f"Trouvé {len(matches)} occurrence(s) : {matches}"
        )

    def test_retrospective_pypi_note_present(self):
        """La note PyPI rétrospective est présente dans api.md (publication beta.5 déjà faite)."""
        text = API_REF.read_text(encoding="utf-8")
        assert "Disponible sur PyPI depuis `1.0.0-beta.5`" in text, (
            "docs/reference/api.md doit mentionner la disponibilité PyPI des opt-ins "
            "rbac/workflow/stats depuis 1.0.0-beta.5 (cf DOCS-VERSION-SWEEP-BETA9-001)."
        )
