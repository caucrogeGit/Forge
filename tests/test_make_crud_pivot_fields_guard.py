"""Garde-fou PIVOT-CRUD-002 — make:crud refuse les pivot.fields[] obligatoires.

make:crud synchronise uniquement les identifiants (source_key + target_key).
Si une table pivot contient des champs obligatoires (required: true ou nullable: false)
non gérés par le CRUD simple, make:crud doit refuser la génération.

Cas acceptés :
- pivot sans fields[]
- pivot.fields[] tous nullable: true
- pivot.fields[] avec required: false (= nullable par défaut)

Cas refusés :
- pivot.fields[] avec required: true
- pivot.fields[] avec nullable: false
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_mvc_entities.make_crud import make_crud, _to_snake


# ── Entités de base ────────────────────────────────────────────────────────────

_ARTICLE = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "article",
    "fields": [{"name": "title", "type": "string", "max_length": 150, "required": True}],
}

_TAG = {
    "schema_version": "1.0",
    "name": "Tag",
    "table": "tag",
    "fields": [{"name": "name", "type": "string", "max_length": 80, "required": True}],
}


def _pivot_relation(fields: list) -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": fields,
                },
            }
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


def _setup(tmp_path: Path, fields: list) -> None:
    _write_entity(tmp_path, _ARTICLE)
    _write_entity(tmp_path, _TAG)
    _write_relations(tmp_path, _pivot_relation(fields))


def _run(tmp_path: Path) -> None:
    make_crud(
        "Article",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )


# ── Cas acceptés ──────────────────────────────────────────────────────────────


def test_pivot_sans_fields_accepte(tmp_path):
    """Un pivot sans champs métier est toujours accepté."""
    _setup(tmp_path, [])
    _run(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_pivot_nullable_true_accepte(tmp_path):
    """Un champ pivot nullable: true est compatible avec le CRUD simple."""
    _setup(tmp_path, [{"name": "note", "type": "text", "nullable": True}])
    _run(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_pivot_required_false_accepte(tmp_path):
    """required: false ne rend pas le champ NOT NULL — compatible avec le CRUD simple."""
    _setup(tmp_path, [{"name": "note", "type": "string", "nullable": True}])
    _run(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_pivot_nullable_absent_accepte(tmp_path):
    """Sans nullable ni required, le champ est nullable par défaut (ADR-013) — accepté."""
    _setup(tmp_path, [{"name": "note", "type": "string", "max_length": 80}])
    _run(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_pivot_plusieurs_champs_nullable_accepte(tmp_path):
    """Plusieurs champs pivot tous nullable sont acceptés."""
    _setup(tmp_path, [
        {"name": "note", "type": "text", "nullable": True},
        {"name": "score", "type": "integer", "nullable": True},
        {"name": "joined_at", "type": "datetime", "nullable": True},
    ])
    _run(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


# ── Cas refusés ───────────────────────────────────────────────────────────────


def test_pivot_required_true_refuse(tmp_path, capsys):
    """required: true rend le champ NOT NULL — incompatible avec le CRUD simple."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "required": True}])
    with pytest.raises(SystemExit) as exc_info:
        _run(tmp_path)
    assert exc_info.value.code == 1


def test_pivot_nullable_false_refuse(tmp_path, capsys):
    """nullable: false rend le champ NOT NULL — incompatible avec le CRUD simple."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    with pytest.raises(SystemExit) as exc_info:
        _run(tmp_path)
    assert exc_info.value.code == 1


# ── Message d'erreur ──────────────────────────────────────────────────────────


def test_message_contient_nom_champ_pivot(tmp_path, capsys):
    """Le message d'erreur mentionne le nom du champ incompatible."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "position" in captured.out


def test_message_contient_make_crud(tmp_path, capsys):
    """Le message d'erreur mentionne make:crud."""
    _setup(tmp_path, [{"name": "role", "type": "string", "required": True}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "make:crud" in captured.out


def test_message_contient_crud_simple_ou_identifiants(tmp_path, capsys):
    """Le message d'erreur mentionne le CRUD simple ou la synchronisation d'identifiants."""
    _setup(tmp_path, [{"name": "role", "type": "string", "required": True}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "CRUD simple" in captured.out or "identifiants" in captured.out


def test_message_contient_pivot_table(tmp_path, capsys):
    """Le message d'erreur mentionne le nom de la table pivot."""
    _setup(tmp_path, [{"name": "role", "type": "string", "required": True}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "article_tag" in captured.out


def test_message_mentionne_tous_champs_incompatibles(tmp_path, capsys):
    """Tous les champs incompatibles sont listés dans le message d'erreur."""
    _setup(tmp_path, [
        {"name": "position", "type": "integer", "nullable": False},
        {"name": "role", "type": "string", "required": True},
        {"name": "note", "type": "text", "nullable": True},
    ])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "position" in captured.out
    assert "role" in captured.out
    assert "note" not in captured.out  # nullable: champ compatible, non mentionné


# ── Aucun fichier généré en cas de refus ─────────────────────────────────────


def test_aucun_fichier_genere_si_refuse(tmp_path, capsys):
    """Si make:crud refuse, aucun fichier CRUD n'est créé."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    assert not (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()
    assert not (tmp_path / "mvc" / "models" / "article_model.py").exists()
    assert not (tmp_path / "mvc" / "views" / "article").exists()


# ── FIELD-FIX-M2M-GUARD-001 — garde limité au côté source ────────────────────


def _run_tag(tmp_path: Path) -> None:
    make_crud(
        "Tag",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )


def test_source_side_still_blocked_for_required_pivot_fields(tmp_path, capsys):
    """Article (côté source) reste bloqué si pivot.fields[] contient un champ non-nullable."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    with pytest.raises(SystemExit) as exc_info:
        _run(tmp_path)
    assert exc_info.value.code == 1


def test_target_side_is_not_blocked_by_source_pivot_fields(tmp_path):
    """Tag (côté inverse) ne doit pas être bloqué par les pivot.fields[] de la relation Article→Tag."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    _run_tag(tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "tag_controller.py").exists()


def test_target_side_generates_full_crud(tmp_path):
    """make:crud Tag génère le CRUD complet même quand le pivot d'Article a des champs obligatoires."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    _run_tag(tmp_path)
    assert (tmp_path / "mvc" / "models" / "tag_model.py").exists()
    assert (tmp_path / "mvc" / "views" / "tag").exists()


def test_error_message_mentions_make_pivot_crud(tmp_path, capsys):
    """Le message d'erreur côté source mentionne make:pivot-crud."""
    _setup(tmp_path, [{"name": "position", "type": "integer", "nullable": False}])
    with pytest.raises(SystemExit):
        _run(tmp_path)
    captured = capsys.readouterr()
    assert "make:pivot-crud" in captured.out


def test_make_pivot_crud_still_works_for_same_relation(tmp_path):
    """make:pivot-crud Article tags reste fonctionnel indépendamment du garde make:crud."""
    from forge_mvc_entities.make_pivot_crud import make_pivot_crud

    _setup(tmp_path, [
        {"name": "position", "type": "integer", "nullable": False},
        {"name": "note", "type": "string", "max_length": 120, "nullable": True},
    ])
    make_pivot_crud(
        "Article",
        "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    assert (tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py").exists()


def test_make_crud_guard_fix_documented(tmp_path):
    """Le rapport FIELD-AUDIT-M2M-GUARD-001 mentionne la correction FIELD-FIX-M2M-GUARD-001."""
    from pathlib import Path as P

    audit = P(__file__).resolve().parents[1] / "docs/history/audits/field-audit-m2m-guard-001.md"
    assert audit.exists()
    assert "FIELD-FIX-M2M-GUARD-001" in audit.read_text()
