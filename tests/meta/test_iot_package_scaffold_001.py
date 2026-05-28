"""Garde-fou IOT-PACKAGE-SCAFFOLD-001.

Vérifie le squelette du package opt-in ``forge-mvc-iot`` :

- structure de fichiers attendue ;
- ``pyproject.toml`` aligné sur les conventions des autres opt-ins ;
- dépendance correcte vers ``forge-mvc`` (et inversement : Forge Core
  ne dépend pas de ``forge-mvc-iot``) ;
- aucune dépendance MQTT déclarée à ce stade ;
- aucun import de ``forge_mvc_iot`` dans ``core/``.

Le test ne contraint pas l'implémentation : il garantit uniquement que
le périmètre du ticket IOT-PACKAGE-SCAFFOLD-001 reste tenu (pas de
glissement vers un broker MQTT, vers une table SQL ou vers Forge Core).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent

IOT_PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-iot"
IOT_PYPROJECT = IOT_PKG_DIR / "pyproject.toml"
IOT_README = IOT_PKG_DIR / "README.md"
IOT_PYTHON_PKG = IOT_PKG_DIR / "forge_mvc_iot"
CORE_DIR = PROJECT_ROOT / "core"
FORGE_PYPROJECT = PROJECT_ROOT / "pyproject.toml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


@pytest.fixture(scope="module")
def iot_pyproject_data() -> dict:
    return tomllib.loads(IOT_PYPROJECT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def forge_pyproject_data() -> dict:
    return tomllib.loads(FORGE_PYPROJECT.read_text(encoding="utf-8"))


class TestPackageStructure:
    """Le package contient les fichiers et sous-dossiers attendus."""

    @pytest.mark.parametrize(
        "rel_path",
        [
            "pyproject.toml",
            "README.md",
            "forge_mvc_iot/__init__.py",
            "forge_mvc_iot/mqtt/__init__.py",
            "forge_mvc_iot/storage/__init__.py",
            "forge_mvc_iot/diagnostics/__init__.py",
        ],
    )
    def test_file_present(self, rel_path: str):
        path = IOT_PKG_DIR / rel_path
        assert path.exists(), f"Fichier manquant : packages/forge-mvc-iot/{rel_path}"

    @pytest.mark.parametrize("sub", ["mqtt", "storage", "diagnostics"])
    def test_subpackage_is_dir(self, sub: str):
        assert (IOT_PYTHON_PKG / sub).is_dir()


class TestPyprojectContract:
    """pyproject.toml respecte les conventions des opt-ins existants."""

    def test_project_name(self, iot_pyproject_data):
        assert iot_pyproject_data["project"]["name"] == "forge-mvc-iot"

    def test_project_version_present(self, iot_pyproject_data):
        version = iot_pyproject_data["project"]["version"]
        assert version, "Le champ version doit être renseigné"

    def test_requires_python_312(self, iot_pyproject_data):
        # ADR-006 — Python 3.12+ minimum.
        rp = iot_pyproject_data["project"]["requires-python"]
        assert "3.12" in rp, f"requires-python doit cibler Python 3.12+ (vu : {rp})"

    def test_dependency_on_forge_mvc(self, iot_pyproject_data):
        deps = iot_pyproject_data["project"]["dependencies"]
        assert any("forge-mvc" in d for d in deps), (
            "Le package doit dépendre de forge-mvc"
        )

    def test_no_paho_mqtt_dependency(self, iot_pyproject_data):
        deps = iot_pyproject_data["project"]["dependencies"]
        for dep in deps:
            assert "paho" not in dep.lower(), (
                f"Aucune dépendance paho-mqtt ne doit être déclarée "
                f"au scaffold (vu : {dep!r})"
            )

    def test_setuptools_finds_forge_mvc_iot(self, iot_pyproject_data):
        include = iot_pyproject_data["tool"]["setuptools"]["packages"]["find"]["include"]
        assert any("forge_mvc_iot" in entry for entry in include), (
            "tool.setuptools.packages.find doit inclure forge_mvc_iot*"
        )


class TestForgeCoreIndependence:
    """Forge Core ne déclare pas de dépendance vers forge-mvc-iot."""

    def test_core_dependencies_do_not_reference_iot(self, forge_pyproject_data):
        deps = forge_pyproject_data["project"].get("dependencies", [])
        for dep in deps:
            assert "forge-mvc-iot" not in dep, (
                f"Forge Core ne doit pas dépendre de forge-mvc-iot (vu : {dep!r})"
            )

    def test_core_optional_dependencies_do_not_reference_iot(
        self, forge_pyproject_data
    ):
        extras = forge_pyproject_data["project"].get("optional-dependencies", {})
        for group, deps in extras.items():
            for dep in deps:
                assert "forge-mvc-iot" not in dep, (
                    f"Le groupe optional-dependencies '{group}' ne doit pas "
                    f"référencer forge-mvc-iot (vu : {dep!r})"
                )

    def test_no_core_module_imports_forge_mvc_iot(self):
        offenders: list[Path] = []
        for py in CORE_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="replace")
            if "forge_mvc_iot" in text:
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, (
            "Aucun fichier sous core/ ne doit importer ou mentionner "
            f"forge_mvc_iot. Fichiers fautifs : {offenders}"
        )


class TestReadme:
    """Le README annonce le statut opt-in et le scaffold."""

    def setup_method(self):
        self.text = IOT_README.read_text(encoding="utf-8")

    def test_mentions_opt_in(self):
        assert "opt-in" in self.text.lower(), (
            "README.md doit annoncer le statut opt-in"
        )

    def test_mentions_mqtt(self):
        assert "MQTT" in self.text

    def test_announces_scaffold_status(self):
        # Une mention explicite que le module n'est pas encore implémenté.
        markers = ("squelette", "scaffold", "pas encore", "non implémenté")
        assert any(m in self.text.lower() for m in markers), (
            "README.md doit indiquer que l'implémentation n'est pas faite"
        )


class TestRoadmapMentions:
    """La roadmap mentionne le ticket IOT-PACKAGE-SCAFFOLD-001."""

    def test_roadmap_lists_ticket(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "IOT-PACKAGE-SCAFFOLD-001" in text, (
            "docs/roadmap/forge-roadmap.md doit lister IOT-PACKAGE-SCAFFOLD-001"
        )


class TestModuleImportable:
    """Le package est importable sans erreur (squelette pur, pas d'effet de bord)."""

    def test_import_root(self):
        import forge_mvc_iot  # noqa: F401

    def test_import_subpackages(self):
        import forge_mvc_iot.mqtt  # noqa: F401
        import forge_mvc_iot.storage  # noqa: F401
        import forge_mvc_iot.diagnostics  # noqa: F401

    def test_version_attribute(self):
        import forge_mvc_iot

        assert isinstance(forge_mvc_iot.__version__, str)
        assert forge_mvc_iot.__version__, "__version__ ne doit pas être vide"
