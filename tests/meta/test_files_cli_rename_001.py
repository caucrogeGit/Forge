"""Garde-fou FILES-CLI-RENAME-001 (ADR-019).

Les générateurs et le CLI ciblent ``forge-mvc-files`` pour l'upload générique, et
le **core CLI n'exige plus l'upload** au démarrage :

- ``controller_builder`` génère ``from forge_mvc_files import save_upload`` pour
  les champs fichier (et plus ``core.uploads``) ;
- ``forge_cli/uploads.py`` importe ``forge_mvc_files`` (opt-in) ;
- ``forge.py`` n'importe **pas** ``forge_cli.uploads`` au niveau module : il le
  fait en *lazy* dans la branche ``upload:init``/``media:init`` (sinon le core
  CLI tomberait sans l'opt-in installé).
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
FORGE_PY = PROJECT_ROOT / "forge.py"
CLI_UPLOADS = PROJECT_ROOT / "forge_cli" / "uploads.py"
CONTROLLER_BUILDER = PROJECT_ROOT / "forge_cli" / "entities" / "crud" / "controller_builder.py"


def test_controller_builder_generates_forge_mvc_files_upload():
    text = CONTROLLER_BUILDER.read_text(encoding="utf-8")
    assert "forge_mvc_files import save_upload" in text
    assert "core.uploads import save_upload" not in text


def test_cli_uploads_imports_forge_mvc_files():
    text = CLI_UPLOADS.read_text(encoding="utf-8")
    assert "forge_mvc_files" in text
    assert "core.uploads" not in text


def test_forge_py_does_not_import_cli_uploads_at_module_level():
    # Le core CLI ne doit pas tirer l'upload (opt-in) au chargement : l'import
    # de forge_cli.uploads doit être *lazy* (dans une fonction), pas top-level.
    tree = ast.parse(FORGE_PY.read_text(encoding="utf-8"))
    for node in tree.body:  # uniquement le niveau module
        if isinstance(node, ast.ImportFrom) and node.module == "forge_cli.uploads":
            pytest.fail(
                "forge.py importe forge_cli.uploads au niveau module — doit être "
                "lazy (l'upload est un opt-in forge-mvc-files)."
            )


def test_forge_py_lazy_imports_cli_uploads_in_branch():
    # L'import lazy existe bien quelque part (dans la branche de commande).
    text = FORGE_PY.read_text(encoding="utf-8")
    assert "from forge_cli.uploads import main" in text
