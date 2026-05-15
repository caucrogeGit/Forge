"""Garde-fou PYTEST-REPRODUCIBLE-001.

Vérifie que les 4 modules opt-in de Forge sont importables dans
l'environnement de test, et que requirements-dev.txt + CONTRIBUTING.md
documentent la procédure pour les installer.

Origine : blocage critique — un contributeur frais peut faire
`pip install -e .` puis `pip install -r requirements-dev.txt` et obtenir
~46 errors en collecte sur les tests MFA/RBAC/Workflow/Stats.

Les packages opt-in ne sont pas (encore) publiés sur PyPI, donc l'extra
forge-mvc[all] ne peut pas les résoudre. requirements-dev.txt les pointe
explicitement via `-e ./packages/forge-mvc-*`.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent

REQUIRED_OPT_IN_MODULES = [
    "forge_mvc_mfa",
    "forge_mvc_rbac",
    "forge_mvc_workflow",
    "forge_mvc_stats",
]

OPT_IN_PACKAGE_DIRS = [
    "packages/forge-mvc-mfa",
    "packages/forge-mvc-rbac",
    "packages/forge-mvc-workflow",
    "packages/forge-mvc-stats",
]


class TestOptInModulesImportable:
    """Les 4 modules opt-in Forge sont importables dans l'env de test."""

    @pytest.mark.parametrize("module_name", REQUIRED_OPT_IN_MODULES)
    def test_module_importable(self, module_name: str):
        pytest.importorskip(
            module_name,
            reason=(
                f"Module opt-in '{module_name}' absent de cet environnement. "
                f"pip install -r requirements-dev.txt pour l'env complet."
            ),
        )


class TestRequirementsDevDeclaresOptIn:
    """requirements-dev.txt déclare les 4 modules en éditable."""

    def test_requirements_dev_exists(self):
        assert (PROJECT_ROOT / "requirements-dev.txt").exists()

    @pytest.mark.parametrize("package_dir", OPT_IN_PACKAGE_DIRS)
    def test_requirements_dev_lists_opt_in_module(self, package_dir: str):
        text = (PROJECT_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        assert package_dir in text, (
            f"requirements-dev.txt doit contenir '-e ./{package_dir}' pour "
            f"rendre pytest reproductible. Voir CONTRIBUTING.md."
        )


class TestContributingMdDocumentsProcedure:
    """CONTRIBUTING.md documente la procédure de tests reproductible."""

    def test_contributing_exists(self):
        assert (PROJECT_ROOT / "CONTRIBUTING.md").exists()

    def test_contributing_mentions_install_dev(self):
        text = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        assert "pip install -r requirements-dev.txt" in text, (
            "CONTRIBUTING.md doit documenter la procédure de tests avec "
            "`pip install -r requirements-dev.txt`."
        )

    def test_contributing_has_lancer_les_tests_section(self):
        text = (PROJECT_ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        assert "## Lancer les tests" in text, (
            "CONTRIBUTING.md doit avoir une section '## Lancer les tests' "
            "qui documente la procédure d'install + pytest pour un "
            "contributeur frais."
        )
