"""Garde-fou AUDIO-MODULE-001 — structure et intégration de forge-mvc-audio.

Vérifie le paquet opt-in ``forge-mvc-audio`` :

- structure de fichiers attendue (modules cœur + CLI) ;
- ``pyproject.toml`` aligné sur les conventions des opt-ins (dépend de forge-mvc,
  pas de dépendance pip ffmpeg) ;
- indépendance du core (le core ne dépend pas de forge-mvc-audio, ne l'importe
  pas au niveau module) ;
- module **sans état** : aucune migration SQL, pas de repository ;
- branchement CLI ``audio:doctor`` dans ``forge.py`` + help ;
- API publique exposée.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PKG_DIR = PROJECT_ROOT / "packages" / "forge-mvc-audio"
PYPROJECT = PKG_DIR / "pyproject.toml"
PY_PKG = PKG_DIR / "forge_mvc_audio"
CORE_DIR = PROJECT_ROOT / "core"
FORGE_PYPROJECT = PROJECT_ROOT / "pyproject.toml"


@pytest.fixture(scope="module")
def pyproject_data() -> dict:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


class TestStructure:
    @pytest.mark.parametrize(
        "rel",
        [
            "pyproject.toml",
            "README.md",
            "forge_mvc_audio/__init__.py",
            "forge_mvc_audio/config.py",
            "forge_mvc_audio/storage.py",
            "forge_mvc_audio/probe.py",
            "forge_mvc_audio/ingest.py",
            "forge_mvc_audio/transcode.py",
            "forge_mvc_audio/http.py",
            "forge_mvc_audio/cli/__init__.py",
            "forge_mvc_audio/cli/doctor.py",
        ],
    )
    def test_file_present(self, rel: str):
        assert (PKG_DIR / rel).exists(), f"manquant : packages/forge-mvc-audio/{rel}"

    def test_no_sql_migration_stateless(self):
        # Module SANS état : pas de dossier migrations ni de .sql.
        assert not (PY_PKG / "migrations").exists()
        assert not list(PY_PKG.rglob("*.sql"))

    def test_no_repository_stateless(self):
        assert not (PY_PKG / "storage" ).is_dir()  # storage est un module plat
        assert not list(PY_PKG.rglob("repository.py"))


class TestPyprojectContract:
    def test_name(self, pyproject_data):
        assert pyproject_data["project"]["name"] == "forge-mvc-audio"

    def test_depends_on_forge_mvc(self, pyproject_data):
        deps = pyproject_data["project"]["dependencies"]
        assert any("forge-mvc" in d for d in deps)

    def test_no_pip_ffmpeg_dependency(self, pyproject_data):
        # ffmpeg/ffprobe sont des binaires système, jamais des deps pip.
        deps = pyproject_data["project"]["dependencies"]
        assert not any("ffmpeg" in d.lower() or "ffprobe" in d.lower() for d in deps)

    def test_requires_python_312(self, pyproject_data):
        assert "3.12" in pyproject_data["project"]["requires-python"]


class TestCoreIndependence:
    def test_core_pyproject_does_not_depend_on_audio(self):
        data = tomllib.loads(FORGE_PYPROJECT.read_text(encoding="utf-8"))
        for dep in data["project"].get("dependencies", []):
            assert "forge-mvc-audio" not in dep

    def test_no_core_module_imports_audio(self):
        offenders = []
        for py in CORE_DIR.rglob("*.py"):
            if "forge_mvc_audio" in py.read_text(encoding="utf-8", errors="replace"):
                offenders.append(py.relative_to(PROJECT_ROOT))
        assert not offenders, f"core/ ne doit pas importer forge_mvc_audio : {offenders}"


class TestApiAndCli:
    def test_public_api(self):
        import forge_mvc_audio

        for name in (
            "register_audio_routes",
            "ingest_audio",
            "probe_audio",
            "transcode_to_mp3",
            "load_audio_config",
        ):
            assert hasattr(forge_mvc_audio, name)

    def test_version(self):
        import forge_mvc_audio

        assert forge_mvc_audio.__version__

    def test_cli_dispatch_in_forge(self):
        # ADR-059 : audio:doctor est dispatchée via la table opt-in centrale.
        from cli.commands.optin_dispatch import all_optin_commands

        commands = all_optin_commands()
        assert "audio:doctor" in commands
        assert commands["audio:doctor"].module == "forge_mvc_audio.cli.doctor"

    def test_help_mentions_audio_doctor(self):
        help_text = (PROJECT_ROOT / "cli" / "_support" / "help.py").read_text(encoding="utf-8")
        assert "audio:doctor" in help_text
        dispatch = (PROJECT_ROOT / "cli" / "_support" / "help_dispatch.py").read_text(
            encoding="utf-8"
        )
        assert "audio:doctor" in dispatch
