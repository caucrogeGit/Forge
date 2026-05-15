"""Garde-fou DOCS-STATS-README-CREATE-001.

Vérifie que chaque package distribué dans packages/ a son propre README.md
et que le pyproject.toml déclare ce README pour PyPI.

Sans ce garde-fou, la page PyPI d'un package affichera 'No README available'
lors de la publication (forge-mvc-stats manquait de README jusqu'à C5).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES_DIR = PROJECT_ROOT / "packages"


def _distributable_packages() -> list[Path]:
    """Sous-dossiers de packages/ qui ont un pyproject.toml."""
    return sorted(
        p for p in PACKAGES_DIR.iterdir()
        if p.is_dir() and (p / "pyproject.toml").exists()
    )


_PACKAGES = _distributable_packages()
_PACKAGE_IDS = [p.name for p in _PACKAGES]


class TestEveryPackageHasReadme:
    """Chaque package livré a son propre README.md."""

    @pytest.mark.parametrize("package_dir", _PACKAGES, ids=_PACKAGE_IDS)
    def test_package_has_readme(self, package_dir: Path):
        readme = package_dir / "README.md"
        assert readme.exists(), (
            f"{package_dir.name} n'a pas de README.md — "
            f"la page PyPI affichera 'No README available' à la publication."
        )

    @pytest.mark.parametrize("package_dir", _PACKAGES, ids=_PACKAGE_IDS)
    def test_readme_starts_with_title(self, package_dir: Path):
        readme = package_dir / "README.md"
        if not readme.exists():
            pytest.skip("README absent — couvert par test_package_has_readme")
        text = readme.read_text(encoding="utf-8")
        assert text.lstrip().startswith("#"), (
            f"{package_dir.name}/README.md ne commence pas par un titre markdown (# ...)"
        )

    @pytest.mark.parametrize("package_dir", _PACKAGES, ids=_PACKAGE_IDS)
    def test_readme_is_non_empty(self, package_dir: Path):
        readme = package_dir / "README.md"
        if not readme.exists():
            pytest.skip("README absent — couvert par test_package_has_readme")
        text = readme.read_text(encoding="utf-8")
        non_empty = [l for l in text.splitlines() if l.strip()]
        assert len(non_empty) >= 6, (
            f"{package_dir.name}/README.md n'a que {len(non_empty)} lignes non vides "
            f"(minimum 6 attendu — titre, description, au moins une section)."
        )


class TestPyprojectDeclaresReadme:
    """Chaque pyproject.toml déclare son README pour PyPI."""

    @pytest.mark.parametrize("package_dir", _PACKAGES, ids=_PACKAGE_IDS)
    def test_pyproject_declares_readme(self, package_dir: Path):
        pyproject = package_dir / "pyproject.toml"
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        project = data.get("project", {})
        readme_field = project.get("readme")
        assert readme_field, (
            f"{package_dir.name}/pyproject.toml ne déclare pas le champ `readme` "
            f"dans [project] — PyPI ne saura pas où trouver la description longue."
        )
        if isinstance(readme_field, str):
            readme_name = readme_field
        elif isinstance(readme_field, dict):
            readme_name = readme_field.get("file", "")
        else:
            readme_name = str(readme_field)
        if readme_name.endswith((".md", ".rst")):
            assert (package_dir / readme_name).exists(), (
                f"{package_dir.name}/pyproject.toml référence `{readme_name}` "
                f"qui n'existe pas."
            )
