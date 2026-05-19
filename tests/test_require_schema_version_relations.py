"""Tests — LEGACY-STRICT-SCHEMA-001 : schema_version obligatoire pour relations.json.

Vérifie que validate_relations_definition et sync_relations refusent les relations
sans schema_version. Ce comportement était déjà en place avant ce ticket ;
ces tests servent de garde-fous de non-régression.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.entities.model import ModelValidationError, build_model, sync_relations
from forge_cli.entities.relations import EntityRelationsError, validate_relations_definition


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data) + "\n", encoding="utf-8")


_ENTITY_CANONIQUE = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "titre", "type": "string", "max_length": 200},
    ],
}

_RELATIONS_SANS_VERSION = {
    "relations": [],
}

_RELATIONS_CANONIQUES = {
    "schema_version": "1.0",
    "relations": [],
}


# ── validate_relations_definition ─────────────────────────────────────────────


def test_validate_relations_refuse_sans_schema_version(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entities_root.mkdir(parents=True)

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _RELATIONS_SANS_VERSION,
            source="relations.json",
            entities_root=entities_root,
        )

    assert "schema_version" in str(exc_info.value)


def test_validate_relations_accepte_schema_version_1_0(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entities_root.mkdir(parents=True)

    validated = validate_relations_definition(
        _RELATIONS_CANONIQUES,
        source="relations.json",
        entities_root=entities_root,
    )
    assert validated == []


# ── sync:relations ────────────────────────────────────────────────────────────


def test_sync_relations_refuse_sans_schema_version(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    entities_root.mkdir(parents=True)
    (entities_root / "relations.json").write_text(
        json.dumps(_RELATIONS_SANS_VERSION), encoding="utf-8"
    )

    with pytest.raises((EntityRelationsError, ValueError)):
        sync_relations(entities_root)


# ── build:model — relations refusées si schema_version absent ─────────────────


def test_build_model_refuse_relations_sans_schema_version(tmp_path: Path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _ENTITY_CANONIQUE)
    (entities_root / "relations.json").write_text(
        json.dumps(_RELATIONS_SANS_VERSION), encoding="utf-8"
    )

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    assert "schema_version" in str(exc_info.value)
