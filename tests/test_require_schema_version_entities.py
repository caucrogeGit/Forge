"""Tests — LEGACY-STRICT-SCHEMA-001 : schema_version obligatoire pour les entités.

Vérifie que build:model et make:crud refusent les entités sans schema_version.
Les entités format_version: 1 sont déjà refusées (LEGACY-REMOVE-001A/001B) ;
ce ticket ferme le cas des entités sans aucun marqueur de version.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_mvc_entities.model import ModelValidationError, build_model, check_model
from forge_mvc_entities.make_crud import make_crud


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data) + "\n", encoding="utf-8")


def _write_relations(root: Path, data: dict) -> None:
    (root / "relations.json").write_text(json.dumps(data) + "\n", encoding="utf-8")


_RELATIONS_VIDES = {"schema_version": "1.0", "relations": []}

_ENTITY_CANONIQUE = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "titre", "type": "string", "max_length": 200},
    ],
}

_ENTITY_SANS_VERSION = {
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "titre", "type": "string", "max_length": 200},
    ],
}


# ── build:model — refus si schema_version absent ──────────────────────────────


def test_build_model_refuse_entite_sans_schema_version(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_SANS_VERSION)
    _write_relations(entities_root, _RELATIONS_VIDES)

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    assert "schema_version" in str(exc_info.value).lower() or "sans schema_version" in str(exc_info.value)


def test_build_model_refuse_entite_sans_version_message_guide(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_SANS_VERSION)
    _write_relations(entities_root, _RELATIONS_VIDES)

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    message = str(exc_info.value)
    assert "migration-legacy-vers-canonique" in message or "schema_version" in message


def test_check_model_refuse_entite_sans_schema_version(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_SANS_VERSION)
    _write_relations(entities_root, _RELATIONS_VIDES)

    with pytest.raises(ModelValidationError) as exc_info:
        check_model(entities_root)

    assert "schema_version" in str(exc_info.value).lower() or "sans schema_version" in str(exc_info.value)


def test_build_model_accepte_entite_canonique(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_CANONIQUE)
    _write_relations(entities_root, _RELATIONS_VIDES)

    result = build_model(entities_root)

    assert entities_root / "article" / "article.sql" in result.written


# ── make:crud — refus si schema_version absent et pas de clé entity ───────────


def test_make_crud_refuse_entite_sans_schema_version_ni_entity(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_SANS_VERSION)
    (entities_root / "relations.json").write_text(
        json.dumps(_RELATIONS_VIDES), encoding="utf-8"
    )

    with pytest.raises(SystemExit) as exc_info:
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)

    assert exc_info.value.code == 1


def test_make_crud_accepte_entite_canonique(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_CANONIQUE)
    (entities_root / "relations.json").write_text(
        json.dumps(_RELATIONS_VIDES), encoding="utf-8"
    )

    result = make_crud("Article", entities_root=entities_root, output_root=tmp_path)

    assert result.dry_run is False
