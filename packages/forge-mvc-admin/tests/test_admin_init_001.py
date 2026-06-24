"""Tests de `forge admin:init` (ADMIN-INIT-COMMAND-001).

La commande prépare `mvc/admin/` : write-if-new, idempotente, et ne touche
jamais un fichier utilisateur modifié (charte §9).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_admin")

from forge_mvc_admin.cli.init import init_admin


def _make_project(tmp_path: Path) -> Path:
    (tmp_path / "mvc").mkdir()
    return tmp_path


def test_cree_la_structure(tmp_path: Path):
    root = _make_project(tmp_path)
    assert init_admin(root) == 0
    assert (root / "mvc" / "admin" / "__init__.py").is_file()
    assert (root / "mvc" / "admin" / "resources.py").is_file()


def test_refuse_hors_projet_forge(tmp_path: Path):
    # Pas de dossier mvc/ : ce n'est pas un projet Forge.
    assert init_admin(tmp_path) == 1
    assert not (tmp_path / "mvc").exists()


def test_idempotent(tmp_path: Path):
    root = _make_project(tmp_path)
    assert init_admin(root) == 0
    resources = root / "mvc" / "admin" / "resources.py"
    original = resources.read_text(encoding="utf-8")
    assert init_admin(root) == 0  # rejouable sans erreur
    assert resources.read_text(encoding="utf-8") == original


def test_ne_pas_ecraser_fichier_modifie(tmp_path: Path):
    root = _make_project(tmp_path)
    assert init_admin(root) == 0
    resources = root / "mvc" / "admin" / "resources.py"
    resources.write_text("# code utilisateur\n", encoding="utf-8")
    assert init_admin(root) == 0
    # Le contenu utilisateur est préservé, jamais écrasé.
    assert resources.read_text(encoding="utf-8") == "# code utilisateur\n"
