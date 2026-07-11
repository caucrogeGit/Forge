"""Scaffold du paquet forge-mvc-fixtures (FIXTURES-SCAFFOLD-001, ADR-074).

Garde-fous structurels : opt-in CLI-only, indépendance du cœur, entrée au
catalogue avec le bon kind/catégorie, aucune API runtime ni migration embarquée.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

forge_mvc_fixtures = pytest.importorskip("forge_mvc_fixtures")

PKG_ROOT = Path(forge_mvc_fixtures.__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / "packages" / "forge-mvc-fixtures"

_CURRENT_VERSION = tomllib.loads(
    (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
)["project"]["version"]


@pytest.fixture()
def pyproject_data() -> dict:
    return tomllib.loads((PKG_DIR / "pyproject.toml").read_text(encoding="utf-8"))


class TestStructure:

    @pytest.mark.parametrize("rel", [
        "pyproject.toml",
        "README.md",
        "LICENSE",
        "forge_mvc_fixtures/__init__.py",
        "forge_mvc_fixtures/commands.py",
        "forge_mvc_fixtures/cli/__init__.py",
        "forge_mvc_fixtures/py.typed",
    ])
    def test_file_present(self, rel: str) -> None:
        assert (PKG_DIR / rel).exists(), f"manquant : packages/forge-mvc-fixtures/{rel}"

    def test_name(self, pyproject_data: dict) -> None:
        assert pyproject_data["project"]["name"] == "forge-mvc-fixtures"

    def test_version_matches_core(self, pyproject_data: dict) -> None:
        assert pyproject_data["project"]["version"] == _CURRENT_VERSION

    def test_depends_on_forge_mvc(self, pyproject_data: dict) -> None:
        deps = pyproject_data["project"]["dependencies"]
        assert any("forge-mvc" in d for d in deps)

    def test_requires_python_312(self, pyproject_data: dict) -> None:
        assert "3.12" in pyproject_data["project"]["requires-python"]

    def test_declares_commands_entry_point(self, pyproject_data: dict) -> None:
        # ADR-059 : la plomberie de découverte des commandes est déclarée dès le
        # scaffold, même si la table est vide (commandes livrées aux tickets suivants).
        eps = pyproject_data["project"]["entry-points"]["forge_mvc.commands"]
        assert eps["forge_mvc_fixtures"] == "forge_mvc_fixtures.commands:COMMANDS"


class TestCliOnly:

    def test_pas_de_migration_embarquee(self) -> None:
        # ADR-074 : l'opt-in peuple des tables déjà provisionnées ; il ne gère pas
        # le schéma et n'embarque donc aucune migration.
        assert not (PKG_ROOT / "migrations").exists(), (
            "forge-mvc-fixtures est CLI-only : pas de migrations embarquées"
        )

    def test_core_n_importe_pas_le_paquet(self) -> None:
        core_dir = REPO_ROOT / "core"
        offenders: list[str] = []
        for path in core_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            if "import forge_mvc_fixtures" in text or "from forge_mvc_fixtures" in text:
                offenders.append(str(path.relative_to(REPO_ROOT)))
        assert not offenders, f"le cœur ne doit pas importer forge_mvc_fixtures : {offenders}"

    def test_racine_ne_depend_pas_du_paquet(self) -> None:
        root = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        for dep in root["project"].get("dependencies", []):
            assert "forge-mvc-fixtures" not in dep


class TestCatalog:

    def test_present_avec_kind_et_categorie(self) -> None:
        from cli.optins.catalog import (
            CATEGORY_OPERATIONS,
            KIND_CLI,
            OFFICIAL_OPTINS,
        )

        assert "fixtures" in OFFICIAL_OPTINS
        opt = OFFICIAL_OPTINS["fixtures"]
        assert opt.package_dist == "forge-mvc-fixtures"
        assert opt.package_import == "forge_mvc_fixtures"
        assert opt.kind == KIND_CLI
        assert opt.category == CATEGORY_OPERATIONS
        assert opt.summary
