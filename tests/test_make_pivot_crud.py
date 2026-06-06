"""Tests — PIVOT-ADVANCED-004 : commande make:pivot-crud.

Aucune connexion MariaDB réelle n'est requise.
Toutes les opérations sur le filesystem utilisent tmp_path.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_pivot")
from forge_mvc_pivot.make_pivot_crud import (
    ResolvedPivotRelation,
    cmd_make_pivot_crud_main,
    make_pivot_crud,
    resolve_pivot_relation,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────

_RELATIONS_WITH_FIELDS = {
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
                "fields": [
                    {"name": "position", "type": "integer", "nullable": False},
                    {"name": "note", "type": "string", "max_length": 120, "nullable": True},
                ],
            },
        }
    ],
}

_RELATIONS_EMPTY_FIELDS = {
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
                "fields": [],
            },
        }
    ],
}

_RELATIONS_NO_PIVOT = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_many",
            "from": "Article",
            "to": "Tag",
            "name": "tags",
        }
    ],
}


def _write_relations(tmp_path: Path, data: dict) -> Path:
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    rel_path.parent.mkdir(parents=True, exist_ok=True)
    rel_path.write_text(json.dumps(data), encoding="utf-8")
    return rel_path


# ── Commande dans l'aide ──────────────────────────────────────────────────────


def test_aide_mentionne_make_pivot_crud():
    from forge_cli.help import build_help
    text = build_help("test")
    assert "make:pivot-crud" in text


# ── resolve_pivot_relation ────────────────────────────────────────────────────


def test_resolve_relation_avec_fields(tmp_path):
    rel_path = _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    result = resolve_pivot_relation("Article", "tags", relations_path=rel_path)
    assert isinstance(result, ResolvedPivotRelation)
    assert result.from_entity == "Article"
    assert result.to_entity == "Tag"
    assert result.pivot_table == "article_tag"
    assert result.from_key == "article_id"
    assert result.to_key == "tag_id"
    assert "position" in result.pivot_fields
    assert "note" in result.pivot_fields


def test_resolve_refuse_relations_json_absent(tmp_path):
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Article", "tags", relations_path=rel_path)


def test_resolve_refuse_relations_json_invalide(tmp_path):
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    rel_path.parent.mkdir(parents=True, exist_ok=True)
    rel_path.write_text("{ invalid json", encoding="utf-8")
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Article", "tags", relations_path=rel_path)


def test_resolve_refuse_entite_source_inconnue(tmp_path):
    rel_path = _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Inconnu", "tags", relations_path=rel_path)


def test_resolve_refuse_relation_inconnue(tmp_path):
    rel_path = _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Article", "inexistant", relations_path=rel_path)


def test_resolve_refuse_pivot_fields_vide(tmp_path):
    rel_path = _write_relations(tmp_path, _RELATIONS_EMPTY_FIELDS)
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Article", "tags", relations_path=rel_path)


def test_resolve_refuse_pivot_absent(tmp_path):
    rel_path = _write_relations(tmp_path, _RELATIONS_NO_PIVOT)
    with pytest.raises(SystemExit):
        resolve_pivot_relation("Article", "tags", relations_path=rel_path)


# ── make_pivot_crud ───────────────────────────────────────────────────────────


def test_make_pivot_crud_cree_controleur(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    result = make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    assert ctrl in result.created
    assert ctrl.exists()


def test_make_pivot_crud_cree_template_index(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    index = tmp_path / "mvc" / "templates" / "pivot" / "article_tags" / "index.html"
    assert index.exists()


def test_make_pivot_crud_cree_template_form(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    form = tmp_path / "mvc" / "templates" / "pivot" / "article_tags" / "form.html"
    assert form.exists()


def test_make_pivot_crud_controleur_mentionne_pivot_advanced_service(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    text = ctrl.read_text(encoding="utf-8")
    assert "PivotAdvancedService" in text


# ── dry-run ───────────────────────────────────────────────────────────────────


def test_dry_run_ne_cree_aucun_fichier(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    result = make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
        dry_run=True,
    )
    assert result.dry_run is True
    ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    assert not ctrl.exists()
    assert len(result.created) > 0  # Fichiers listés mais non créés


# ── non-écrasement ────────────────────────────────────────────────────────────


def test_non_ecrasement_par_defaut(tmp_path):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    # Première génération
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
    ctrl.write_text("# contenu modifié", encoding="utf-8")

    # Deuxième génération — ne doit pas écraser
    result = make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
    )
    assert ctrl in result.preserved
    assert ctrl.read_text(encoding="utf-8") == "# contenu modifié"


# ── cmd_make_pivot_crud_main ──────────────────────────────────────────────────


def test_cmd_args_manquants_exit_1(capsys):
    with pytest.raises(SystemExit) as exc_info:
        from forge_mvc_pivot.make_pivot_crud import cmd_make_pivot_crud_main
        cmd_make_pivot_crud_main([])
    assert exc_info.value.code == 1


def test_cmd_option_inconnue_exit_1(tmp_path, capsys):
    _write_relations(tmp_path, _RELATIONS_WITH_FIELDS)
    import os
    orig = os.getcwd()
    os.chdir(tmp_path)
    try:
        with pytest.raises(SystemExit) as exc_info:
            cmd_make_pivot_crud_main(["Article", "tags", "--option-inconnue"])
        assert exc_info.value.code == 1
    finally:
        os.chdir(orig)


# ── Neutralité make:crud ──────────────────────────────────────────────────────


def test_make_crud_non_modifie():
    from forge_cli.entities import make_crud as mc_mod
    import inspect
    src = inspect.getsource(mc_mod)
    assert "make:pivot-crud" not in src
    assert "make_pivot_crud" not in src
    assert "PivotAdvancedService" not in src


# ── Schémas JSON non modifiés ─────────────────────────────────────────────────


def test_schemas_non_modifies():
    schema_path = Path("schemas") / "relations.schema.json"
    assert schema_path.exists()
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    assert data.get("$id") == "https://forge-mvc.dev/schemas/relations.schema.json"
