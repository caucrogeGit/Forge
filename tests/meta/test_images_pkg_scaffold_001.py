"""Garde-fou IMAGES-PKG-SCAFFOLD-001.

Vérifie le squelette du paquet opt-in ``forge-mvc-images`` (ADR-018) :

- structure de fichiers attendue ;
- ``pyproject.toml`` aligné sur les conventions des autres opt-ins ;
- dépendance vers ``forge-mvc`` **et** vers Pillow (le traitement d'image
  devient propriété du module — Pillow quittera le core au ticket
  ``CORE-DROP-PILLOW-001``) ;
- indépendance du core (le core ne dépend pas de ``forge-mvc-images`` et
  aucun fichier ``core/`` ne l'importe) ;
- README annonçant le statut opt-in, le ticket de scaffold et l'ADR-018 ;
- paquet importable, ``__version__`` synchronisé avec le core.

À ce stade (scaffold pur), le test garantit le périmètre du ticket : aucune
logique image/applicative n'est encore déplacée — ces déplacements relèvent
de ``IMAGES-MOVE-PROCESSING-001`` et ``IMAGES-MOVE-APPLICATIVE-001``.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

IMAGES_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-images"
IMAGES_PYPROJECT = IMAGES_PKG_DIR / "pyproject.toml"
IMAGES_README = IMAGES_PKG_DIR / "README.md"
IMAGES_INIT = IMAGES_PKG_DIR / "forge_mvc_images" / "__init__.py"
CORE_DIR = PROJECT_ROOT / "core"
FORGE_PYPROJECT = PROJECT_ROOT / "pyproject.toml"

_CURRENT_VERSION = tomllib.loads(
    FORGE_PYPROJECT.read_text(encoding="utf-8")
)["project"]["version"]


@pytest.fixture(scope="module")
def images_pyproject_data() -> dict:
    return tomllib.loads(IMAGES_PYPROJECT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def forge_pyproject_data() -> dict:
    return tomllib.loads(FORGE_PYPROJECT.read_text(encoding="utf-8"))


class TestPackageStructure:
    """Le paquet contient les fichiers attendus du squelette."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "pyproject.toml",
            "README.md",
            "forge_mvc_images/__init__.py",
        ],
    )
    def test_file_present(self, rel_path: str):
        path = IMAGES_PKG_DIR / rel_path
        assert path.exists(), (
            f"Fichier manquant : packages/forge-mvc-images/{rel_path}"
        )


class TestPyprojectContract:
    """pyproject.toml respecte les conventions des opt-ins existants."""

    def test_project_name(self, images_pyproject_data):
        assert images_pyproject_data["project"]["name"] == "forge-mvc-images"

    def test_version_matches_core(self, images_pyproject_data):
        assert images_pyproject_data["project"]["version"] == _CURRENT_VERSION, (
            "forge-mvc-images doit être synchronisé sur la version du core "
            f"({_CURRENT_VERSION})."
        )

    def test_requires_python_312(self, images_pyproject_data):
        # ADR-006 — Python 3.12+ minimum.
        rp = images_pyproject_data["project"]["requires-python"]
        assert "3.12" in rp, f"requires-python doit cibler Python 3.12+ (vu : {rp})"

    def test_dependency_on_forge_mvc(self, images_pyproject_data):
        deps = images_pyproject_data["project"]["dependencies"]
        assert any("forge-mvc" in d for d in deps), (
            "Le paquet doit dépendre de forge-mvc."
        )

    def test_dependency_on_pillow(self, images_pyproject_data):
        # ADR-018 : Pillow devient dépendance de forge-mvc-images.
        deps = images_pyproject_data["project"]["dependencies"]
        assert any("Pillow" in d or "pillow" in d for d in deps), (
            "forge-mvc-images doit dépendre de Pillow (traitement d'image)."
        )

    def test_setuptools_finds_forge_mvc_images(self, images_pyproject_data):
        include = images_pyproject_data["tool"]["setuptools"]["packages"]["find"][
            "include"
        ]
        assert any("forge_mvc_images" in entry for entry in include), (
            "tool.setuptools.packages.find doit inclure forge_mvc_images*."
        )

    def test_no_private_do_not_upload(self, images_pyproject_data):
        classifiers = images_pyproject_data["project"]["classifiers"]
        assert not any("Private :: Do Not Upload" in c for c in classifiers), (
            "forge-mvc-images ne doit pas porter 'Private :: Do Not Upload'."
        )


class TestForgeCoreIndependence:
    """Le core reste indépendant de l'opt-in forge-mvc-images."""

    def test_core_dependencies_do_not_reference_images(self, forge_pyproject_data):
        deps = forge_pyproject_data["project"].get("dependencies", [])
        for dep in deps:
            assert "forge-mvc-images" not in dep, (
                f"Forge Core ne doit pas dépendre de forge-mvc-images (vu : {dep!r})."
            )

    def test_core_optional_dependencies_do_not_reference_images(
        self, forge_pyproject_data
    ):
        extras = forge_pyproject_data["project"].get("optional-dependencies", {})
        for group, deps in extras.items():
            for dep in deps:
                assert "forge-mvc-images" not in dep, (
                    f"Le groupe optional-dependencies '{group}' ne doit pas "
                    f"référencer forge-mvc-images (vu : {dep!r})."
                )

    def test_no_core_module_imports_forge_mvc_images(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_images" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, (
            "Aucun fichier sous core/ ne doit importer ou mentionner "
            f"forge_mvc_images. Fichiers fautifs : {offenders}"
        )


class TestReadme:
    """Le README annonce le statut opt-in, le scaffold et l'ADR-018."""

    def setup_method(self):
        self.text = IMAGES_README.read_text(encoding="utf-8")

    def test_mentions_opt_in(self):
        assert "opt-in" in self.text.lower(), (
            "README.md doit annoncer le statut opt-in."
        )

    def test_mentions_scaffold_ticket(self):
        assert "IMAGES-PKG-SCAFFOLD-001" in self.text, (
            "README.md doit mentionner le ticket de scaffold."
        )

    def test_mentions_adr_018(self):
        assert "ADR-018" in self.text or "018-image-module-extraction" in self.text, (
            "README.md doit référencer l'ADR-018."
        )


class TestModuleImportable:
    """Le paquet est importable sans effet de bord (squelette pur)."""

    def test_import_root(self):
        import forge_mvc_images  # noqa: F401

    def test_version_attribute(self):
        import forge_mvc_images

        assert isinstance(forge_mvc_images.__version__, str)
        assert forge_mvc_images.__version__ == _CURRENT_VERSION, (
            "forge_mvc_images.__version__ doit être synchronisé avec le core."
        )

    def test_scaffold_has_no_public_api_yet(self):
        # Périmètre du ticket : aucune logique déplacée à ce stade.
        import forge_mvc_images

        assert forge_mvc_images.__all__ == [], (
            "Au stade scaffold, forge_mvc_images ne doit exposer aucune API "
            "(les déplacements relèvent des tickets IMAGES-MOVE-*)."
        )
