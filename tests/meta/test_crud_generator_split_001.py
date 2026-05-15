"""Tests pour CRUD-GENERATOR-SPLIT-001 — Découpage make_crud.py en sous-modules."""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
CRUD_PKG = ROOT / "forge_cli" / "entities" / "crud"


# ── Présence des sous-modules ─────────────────────────────────────────────────


def test_crud_submodule_package_exists():
    """forge_cli/entities/crud/ existe en tant que package Python."""
    assert (CRUD_PKG / "__init__.py").exists()


def test_crud_submodule_context_exists():
    """forge_cli/entities/crud/context.py existe."""
    assert (CRUD_PKG / "context.py").exists()


def test_crud_submodule_utils_exists():
    """forge_cli/entities/crud/utils.py existe."""
    assert (CRUD_PKG / "utils.py").exists()


def test_crud_submodule_relations_loader_exists():
    """forge_cli/entities/crud/relations_loader.py existe."""
    assert (CRUD_PKG / "relations_loader.py").exists()


def test_crud_submodule_form_builder_exists():
    """forge_cli/entities/crud/form_builder.py existe."""
    assert (CRUD_PKG / "form_builder.py").exists()


def test_crud_submodule_model_builder_exists():
    """forge_cli/entities/crud/model_builder.py existe."""
    assert (CRUD_PKG / "model_builder.py").exists()


def test_crud_submodule_controller_builder_exists():
    """forge_cli/entities/crud/controller_builder.py existe."""
    assert (CRUD_PKG / "controller_builder.py").exists()


def test_crud_submodule_views_builder_exists():
    """forge_cli/entities/crud/views_builder.py existe."""
    assert (CRUD_PKG / "views_builder.py").exists()


# ── Taille de la façade ───────────────────────────────────────────────────────


def test_make_crud_facade_is_small():
    """make_crud.py est une façade légère (< 400 lignes)."""
    facade = ROOT / "forge_cli" / "entities" / "make_crud.py"
    lines = facade.read_text(encoding="utf-8").splitlines()
    assert len(lines) < 400, f"make_crud.py fait {len(lines)} lignes, attendu < 400"


# ── Compatibilité imports backward ────────────────────────────────────────────


def test_make_crud_exports_make_crud():
    """forge_cli.entities.make_crud exporte la fonction make_crud."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "make_crud", None))


def test_make_crud_exports_build_controller():
    """forge_cli.entities.make_crud exporte build_controller."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_controller", None))


def test_make_crud_exports_build_model():
    """forge_cli.entities.make_crud exporte build_model."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_model", None))


def test_make_crud_exports_build_form():
    """forge_cli.entities.make_crud exporte build_form."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_form", None))


def test_make_crud_exports_build_index_view():
    """forge_cli.entities.make_crud exporte build_index_view."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_index_view", None))


def test_make_crud_exports_build_show_view():
    """forge_cli.entities.make_crud exporte build_show_view."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_show_view", None))


def test_make_crud_exports_build_form_view():
    """forge_cli.entities.make_crud exporte build_form_view."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "build_form_view", None))


def test_make_crud_exports_MakeCrudResult():
    """forge_cli.entities.make_crud exporte MakeCrudResult."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert getattr(mod, "MakeCrudResult", None) is not None


def test_make_crud_exports_to_snake():
    """forge_cli.entities.make_crud exporte _to_snake."""
    mod = importlib.import_module("forge_cli.entities.make_crud")
    assert callable(getattr(mod, "_to_snake", None))


# ── Imports directs depuis les sous-modules ───────────────────────────────────


def test_crud_context_importable():
    """forge_cli.entities.crud.context est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.context")
    assert hasattr(mod, "MakeCrudResult")
    assert hasattr(mod, "_with_permission")


def test_crud_utils_importable():
    """forge_cli.entities.crud.utils est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.utils")
    assert hasattr(mod, "_to_snake")
    assert hasattr(mod, "_pk_field")


def test_crud_relations_loader_importable():
    """forge_cli.entities.crud.relations_loader est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.relations_loader")
    assert hasattr(mod, "_load_crud_many_to_one_relations")


def test_crud_form_builder_importable():
    """forge_cli.entities.crud.form_builder est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.form_builder")
    assert hasattr(mod, "build_form")


def test_crud_model_builder_importable():
    """forge_cli.entities.crud.model_builder est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.model_builder")
    assert hasattr(mod, "build_model")


def test_crud_controller_builder_importable():
    """forge_cli.entities.crud.controller_builder est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.controller_builder")
    assert hasattr(mod, "build_controller")


def test_crud_views_builder_importable():
    """forge_cli.entities.crud.views_builder est importable."""
    mod = importlib.import_module("forge_cli.entities.crud.views_builder")
    assert hasattr(mod, "build_index_view")
    assert hasattr(mod, "build_show_view")
    assert hasattr(mod, "build_form_view")
    assert hasattr(mod, "build_layout")


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_reference_crud_generator_split_001():
    """forge-roadmap.md référence CRUD-GENERATOR-SPLIT-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "CRUD-GENERATOR-SPLIT-001" in content
