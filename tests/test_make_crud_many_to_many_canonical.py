"""CRUD-M2M-CANONICAL-001 — make:crud avec des relations many_to_many canoniques.

Vérifie que _load_crud_many_to_many_relations() reconnaît
ValidatedCanonicalManyToManyRelation (schema_version 1.0) au même titre que
ValidatedManyToManyRelation (legacy).
"""

from __future__ import annotations

import json
from pathlib import Path

from forge_cli.entities.make_crud import make_crud, _to_snake


MEMBER_CANONICAL = {
    "schema_version": "1.0",
    "name": "Member",
    "table": "members",
    "fields": [
        {"name": "username", "type": "string", "max_length": 80, "required": True},
    ],
}

PROJECT_CANONICAL = {
    "schema_version": "1.0",
    "name": "Project",
    "table": "projects",
    "fields": [
        {"name": "title", "type": "string", "max_length": 150, "required": True},
    ],
}

TAG_CANONICAL = {
    "schema_version": "1.0",
    "name": "Tag",
    "table": "tags",
    "fields": [
        {"name": "name", "type": "string", "max_length": 80, "required": True},
    ],
}

RELATIONS_CANONICAL = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_many",
            "from": "Member",
            "to": "Project",
            "name": "projects",
            "pivot": {
                "table": "member_project",
                "from_key": "member_id",
                "to_key": "project_id",
                "id": True,
                "unique_pair": True,
                "on_delete": "cascade",
                "fields": [],
            },
        }
    ],
}

RELATIONS_CANONICAL_WITH_PIVOT_FIELDS = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_many",
            "from": "Member",
            "to": "Project",
            "name": "projects",
            "pivot": {
                "table": "member_project",
                "from_key": "member_id",
                "to_key": "project_id",
                "id": True,
                "unique_pair": True,
                "on_delete": "cascade",
                "fields": [
                    {"name": "role", "type": "string", "max_length": 50, "nullable": True},
                    {"name": "joined_at", "type": "datetime", "nullable": True},
                ],
            },
        }
    ],
}

RELATIONS_CANONICAL_TWO_M2M = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_many",
            "from": "Member",
            "to": "Project",
            "name": "projects",
            "pivot": {
                "table": "member_project",
                "from_key": "member_id",
                "to_key": "project_id",
                "id": True,
                "unique_pair": True,
                "on_delete": "cascade",
                "fields": [],
            },
        },
        {
            "type": "many_to_many",
            "from": "Member",
            "to": "Tag",
            "name": "tags",
            "pivot": {
                "table": "member_tag",
                "from_key": "member_id",
                "to_key": "tag_id",
                "id": True,
                "unique_pair": True,
                "on_delete": "cascade",
                "fields": [],
            },
        },
    ],
}


def _write_entity(tmp_path: Path, definition: dict) -> None:
    snake = _to_snake(definition["name"])
    entity_dir = tmp_path / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


def _write_relations(tmp_path: Path, relations: dict) -> None:
    entities_root = tmp_path / "mvc" / "entities"
    entities_root.mkdir(parents=True, exist_ok=True)
    (entities_root / "relations.json").write_text(json.dumps(relations), encoding="utf-8")


def _run(tmp_path: Path, entity_name: str, extra_entities: list[dict] | None = None,
         relations: dict | None = None) -> Path:
    _write_entity(tmp_path, MEMBER_CANONICAL)
    _write_entity(tmp_path, PROJECT_CANONICAL)
    for extra in extra_entities or []:
        _write_entity(tmp_path, extra)
    _write_relations(tmp_path, relations or RELATIONS_CANONICAL)
    entities_root = tmp_path / "mvc" / "entities"
    make_crud(entity_name, entities_root=entities_root, output_root=tmp_path)
    return tmp_path


def _read(tmp_path: Path, path: str) -> str:
    return (tmp_path / path).read_text(encoding="utf-8")


# ── Détection de la relation canonique M2M ────────────────────────────────────

def test_make_crud_canonical_m2m_genere_select_multiple(tmp_path):
    _run(tmp_path, "Member")

    form_html = _read(tmp_path, "mvc/views/member/form.html")

    assert "<select" in form_html
    assert "multiple" in form_html
    assert 'name="project_ids"' in form_html
    assert "{% for value, label in project_choices %}" in form_html
    assert "project_ids_selected" in form_html


def test_make_crud_canonical_m2m_genere_fonctions_controller(tmp_path):
    _run(tmp_path, "Member")

    controller = _read(tmp_path, "mvc/controllers/member_controller.py")

    assert "get_project_choices()" in controller
    assert "get_member_project_ids" in controller
    assert "sync_member_project_ids" in controller


def test_make_crud_canonical_m2m_ignore_cote_target(tmp_path):
    _run(tmp_path, "Project")

    form_html = _read(tmp_path, "mvc/views/project/form.html")

    assert 'name="member_ids"' not in form_html
    assert 'name="project_ids"' not in form_html


# ── Robustesse avec pivot.fields[] ────────────────────────────────────────────

def test_make_crud_canonical_m2m_avec_pivot_fields_ne_plante_pas(tmp_path):
    _run(tmp_path, "Member", relations=RELATIONS_CANONICAL_WITH_PIVOT_FIELDS)

    form_html = _read(tmp_path, "mvc/views/member/form.html")

    assert 'name="project_ids"' in form_html


def test_make_crud_canonical_m2m_deux_relations_genere_deux_selects(tmp_path):
    _run(tmp_path, "Member", extra_entities=[TAG_CANONICAL],
         relations=RELATIONS_CANONICAL_TWO_M2M)

    form_html = _read(tmp_path, "mvc/views/member/form.html")

    assert 'name="project_ids"' in form_html
    assert 'name="tag_ids"' in form_html
    assert form_html.count("<select") >= 2
