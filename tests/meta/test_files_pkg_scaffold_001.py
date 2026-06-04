"""Garde-fou FILES-PKG-SCAFFOLD-001 (ADR-019).

Vérifie le squelette du paquet opt-in ``forge-mvc-files`` :

- structure de fichiers attendue ;
- ``pyproject.toml`` aligné sur les conventions des opt-ins (dépend de forge-mvc,
  pas de dépendance pip superflue) ;
- indépendance du core (le core ne dépend pas de forge-mvc-files, ne l'importe
  pas au niveau module) ;
- enregistrement opt-in (catalogue, KIND_LIBRARY) ;
- paquet importable, ``__version__`` synchronisé, **aucune logique déplacée**
  encore (squelette : le pipeline d'upload est déplacé par FILES-MOVE-PIPELINE-001).
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-files"
PYPROJECT = PKG_DIR / "pyproject.toml"
INIT = PKG_DIR / "forge_mvc_files" / "__init__.py"
README = PKG_DIR / "README.md"
CORE_DIR = PROJECT_ROOT / "core"
FORGE_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_CURRENT_VERSION = tomllib.loads(
    FORGE_PYPROJECT.read_text(encoding="utf-8")
)["project"]["version"]


@pytest.fixture(scope="module")
def pyproject_data() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


class TestStructure:
    @pytest.mark.parametrize(
        "rel", ["pyproject.toml", "README.md", "forge_mvc_files/__init__.py"]
    )
    def test_file_present(self, rel: str):
        assert (PKG_DIR / rel).exists(), f"manquant : packages/forge-mvc-files/{rel}"


class TestPyprojectContract:
    def test_name(self, pyproject_data):
        assert pyproject_data["project"]["name"] == "forge-mvc-files"

    def test_version_matches_core(self, pyproject_data):
        assert pyproject_data["project"]["version"] == _CURRENT_VERSION

    def test_depends_on_forge_mvc(self, pyproject_data):
        deps = pyproject_data["project"]["dependencies"]
        assert any("forge-mvc" in d for d in deps)

    def test_requires_python_312(self, pyproject_data):
        assert "3.12" in pyproject_data["project"]["requires-python"]


class TestCoreIndependence:
    def test_core_pyproject_does_not_depend_on_files(self):
        data = tomllib.loads(FORGE_PYPROJECT.read_text(encoding="utf-8"))
        for dep in data["project"].get("dependencies", []):
            assert "forge-mvc-files" not in dep

    def test_no_core_module_hard_imports_files(self):
        # FILES-MOVE-PIPELINE-001 : les shims transitoires de core/uploads/
        # réexportent forge_mvc_files (et sont supprimés au ticket 7). Le core
        # PROPRE (hors ces shims) ne doit pas en dépendre (ADR-004).
        offenders = []
        for py in CORE_DIR.rglob("*.py"):
            if py.parent.name == "uploads":
                continue  # shims transitoires autorisés
            for lineno, line in enumerate(
                py.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                stripped = line.lstrip()
                if stripped.startswith("#"):
                    continue
                if line == stripped and (
                    stripped.startswith("import forge_mvc_files")
                    or stripped.startswith("from forge_mvc_files")
                ):
                    offenders.append(f"{py.relative_to(PROJECT_ROOT)}:{lineno}")
        assert not offenders, f"core/ (hors shims uploads) importe forge_mvc_files : {offenders}"


class TestOptinRegistration:
    def test_in_catalog_as_library(self):
        from forge_cli.optins.catalog import OFFICIAL_OPTINS

        assert "files" in OFFICIAL_OPTINS
        optin = OFFICIAL_OPTINS["files"]
        assert optin.package_dist == "forge-mvc-files"
        assert optin.package_import == "forge_mvc_files"


class TestModuleImportable:
    def test_import_and_version(self):
        import forge_mvc_files

        assert forge_mvc_files.__version__ == _CURRENT_VERSION
