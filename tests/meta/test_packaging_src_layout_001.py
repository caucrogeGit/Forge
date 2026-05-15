"""Garde-fou PACKAGING-SRC-LAYOUT-001.

Vérifie que :
1. Le pyproject.toml racine est la seule source de vérité pour la
   publication PyPI (Approche B — consolidation T2b).
2. La configuration setuptools du pyproject.toml racine est correcte
   (where=["."], include core/forge_cli/integrations).
3. L'ancien véhicule packages/forge-mvc/pyproject.toml n'est pas
   revenu (garde-fou anti-régression).
4. Les artefacts gitignorés générés par l'ancien build vehicle ne
   sont pas physiquement présents dans le repo.

Origine : T2 a découvert que les wheels buildées depuis packages/forge-mvc/
étaient vides (3.6 KB, 0 ligne de code Python). T2b consolide le
packaging sur le pyproject.toml racine qui utilise where=["."] et
produit une wheel valide (~900 KB, core/forge_cli/integrations inclus).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
ROOT_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
OLD_PYPI_PYPROJECT = PROJECT_ROOT / "packages" / "forge-mvc" / "pyproject.toml"

# Artefacts de l'ancien build vehicle (packages/forge-mvc/ avec where=["../.."])
# Supprimés par T2b — ne doivent jamais réapparaître dans packages/
OLD_BUILD_ARTIFACT_PATHS = [
    "packages/core",
    "packages/forge_cli",
    "packages/integrations",
    "packages/forge.py",
]


class TestRootPyprojectIsPublicationSource:
    """Le pyproject.toml racine est la source unique pour la publication PyPI."""

    def test_root_pyproject_exists(self):
        assert ROOT_PYPROJECT.exists(), "pyproject.toml racine manquant"

    def test_old_pypi_pyproject_removed(self):
        assert not OLD_PYPI_PYPROJECT.exists(), (
            "packages/forge-mvc/pyproject.toml a été ressuscité. "
            "Depuis T2b, le pyproject.toml racine est le seul véhicule "
            "de publication PyPI. Supprimer ce fichier pour éviter la confusion."
        )


class TestRootPyprojectSetuptoolsConfig:
    """Le pyproject.toml racine déclare une config setuptools correcte."""

    def _load(self) -> dict:
        return tomllib.loads(ROOT_PYPROJECT.read_text(encoding="utf-8"))

    def test_has_setuptools_section(self):
        data = self._load()
        assert "tool" in data and "setuptools" in data["tool"], (
            "pyproject.toml racine doit avoir [tool.setuptools]."
        )

    def test_packages_find_where_is_dot(self):
        data = self._load()
        where = data["tool"]["setuptools"]["packages"]["find"]["where"]
        assert "." in where, (
            "pyproject.toml racine : [tool.setuptools.packages.find] where doit "
            "contenir '.' pour que python -m build depuis la racine trouve les packages."
        )

    def test_packages_find_includes_core(self):
        data = self._load()
        include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("core" in p for p in include), (
            "pyproject.toml racine : include doit contenir 'core*'."
        )

    def test_packages_find_includes_forge_cli(self):
        data = self._load()
        include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("forge_cli" in p for p in include), (
            "pyproject.toml racine : include doit contenir 'forge_cli*'."
        )

    def test_packages_find_includes_integrations(self):
        data = self._load()
        include = data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("integrations" in p for p in include), (
            "pyproject.toml racine : include doit contenir 'integrations*'."
        )

    def test_has_py_modules_forge(self):
        data = self._load()
        py_modules = data["tool"]["setuptools"].get("py-modules", [])
        assert "forge" in py_modules, (
            "pyproject.toml racine : py-modules doit déclarer 'forge' "
            "pour inclure forge.py dans la wheel."
        )

    def test_pyotp_not_in_root(self):
        data = self._load()
        deps = data.get("project", {}).get("dependencies", [])
        names = {d.split(">=")[0].split("==")[0].strip().lower() for d in deps}
        assert "pyotp" not in names, (
            "pyotp est spécifique à MFA (ADR-004). Doit être déclaré "
            "uniquement dans packages/forge-mvc-mfa/pyproject.toml."
        )


class TestOldBuildArtifactsAbsent:
    """Les artefacts de l'ancien build vehicle ne sont pas présents."""

    @pytest.mark.parametrize("artifact_path", OLD_BUILD_ARTIFACT_PATHS)
    def test_old_build_artifact_absent(self, artifact_path: str):
        path = PROJECT_ROOT / artifact_path
        assert not path.exists(), (
            f"L'ancien artefact '{artifact_path}' est physiquement présent. "
            f"Ces dossiers étaient régénérés par l'ancien "
            f"`python -m build packages/forge-mvc/` (T2b l'a supprimé). "
            f"Supprimer : rm -rf {path}"
        )
