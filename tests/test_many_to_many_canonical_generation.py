"""Garde-fou ENTITY-CONTRACT-016-MANY-TO-MANY-CANONICAL-GENERATION.

Vérifie que make:relation génère le format canonique many_to_many avec un
bloc pivot (id/unique_pair), que validate_relations_definition le valide,
et que generate_relations_sql produit un CREATE TABLE complet.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from forge_mvc_entities import make_relation
from forge_mvc_entities.relations import (
    EntityRelationsError,
    ValidatedCanonicalManyToManyRelation,
    generate_relations_sql,
    validate_relations_definition,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _minimal_entity(name: str, table: str) -> dict:
    return {
        "format_version": 1,
        "entity": name,
        "table": table,
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            }
        ],
    }


def _setup_entities(tmp_path: Path) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "contact", _minimal_entity("Contact", "contact"))
    _write_entity(entities_root, "groupe", _minimal_entity("Groupe", "groupe"))
    return entities_root


def _canonical_m2m_relation(
    from_entity: str = "Contact",
    to_entity: str = "Groupe",
    *,
    name: str = "groupes",
    pivot_table: str = "contact_groupe",
    from_key: str = "contact_id",
    to_key: str = "groupe_id",
    on_delete: str = "cascade",
) -> dict[str, Any]:
    return {
        "type": "many_to_many",
        "from": from_entity,
        "to": to_entity,
        "name": name,
        "pivot": {
            "table": pivot_table,
            "from_key": from_key,
            "to_key": to_key,
            "id": True,
            "unique_pair": True,
            "on_delete": on_delete,
            "fields": [],
        },
    }


def _relations_document(relation: dict) -> dict:
    return {"schema_version": "1.0", "relations": [relation]}


def _run_make_relation_m2m(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    entities_root: Path,
    *,
    from_entity: str = "Contact",
    to_entity: str = "Groupe",
    name: str = "",
    inverse_name: str = "",
    pivot_table: str = "",
    from_key: str = "",
    to_key: str = "",
    on_delete: str = "",
    pivot_fields: "list[str] | None" = None,
    confirm: str = "o",
) -> None:
    monkeypatch.chdir(tmp_path)
    answers = iter([
        "many_to_many",
        from_entity,
        to_entity,
        name,
        inverse_name,
        pivot_table,
        from_key,
        to_key,
        on_delete,
        # ENTITIES-PIVOT-FIELDS-001 : le dialogue demande désormais les attributs
        # du pivot, un par ligne, une réponse vide terminant la saisie. Le défaut
        # ci-dessous n'en déclare aucun, donc le pivot reste simple comme avant.
        *(pivot_fields or []),
        "",
        confirm,
    ])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))
    make_relation.main([])


# ── make:relation écrit relations.json avec le bon format ─────────────────────

def test_make_relation_m2m_creates_relations_json(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    assert (entities_root / "relations.json").exists()


def test_make_relation_m2m_schema_version_is_1_0(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"


def test_make_relation_m2m_type_is_many_to_many(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["type"] == "many_to_many"


def test_make_relation_m2m_from_entity(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["from"] == "Contact"


def test_make_relation_m2m_to_entity(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["to"] == "Groupe"


def test_make_relation_m2m_default_name(monkeypatch, tmp_path):
    """Le nom par défaut est to_snake(to_entity) + 's'."""
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["name"] == "groupes"


def test_make_relation_m2m_pivot_id_is_true(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["id"] is True


def test_make_relation_m2m_pivot_unique_pair_is_true(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["unique_pair"] is True


def test_make_relation_m2m_default_pivot_table(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["table"] == "contact_groupe"


def test_make_relation_m2m_default_from_key(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["from_key"] == "contact_id"


def test_make_relation_m2m_default_to_key(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["to_key"] == "groupe_id"


def test_make_relation_m2m_default_on_delete(monkeypatch, tmp_path):
    """on_delete par défaut est 'cascade' (minuscule)."""
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["on_delete"] == "cascade"


def test_make_relation_m2m_pivot_fields_is_empty_list(monkeypatch, tmp_path):
    """pivot.fields vaut [] — les champs métier du pivot ne sont pas gérés par le wizard."""
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0]["pivot"]["fields"] == []


def test_make_relation_m2m_no_legacy_keys(monkeypatch, tmp_path):
    """La relation canonique ne contient pas de clés legacy (from_entity, etc.)."""
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root)
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    relation = data["relations"][0]
    assert "from_entity" not in relation
    assert "to_entity" not in relation
    assert "from_field" not in relation
    assert "to_field" not in relation
    assert "foreign_key_name" not in relation


def test_make_relation_m2m_inverse_name_optional(monkeypatch, tmp_path):
    """inverse_name est absent si non renseigné."""
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root, inverse_name="")
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert "inverse_name" not in data["relations"][0]


def test_make_relation_m2m_inverse_name_present_when_given(monkeypatch, tmp_path):
    entities_root = _setup_entities(tmp_path)
    _run_make_relation_m2m(monkeypatch, tmp_path, entities_root, inverse_name="contacts")
    data = json.loads((entities_root / "relations.json").read_text(encoding="utf-8"))
    assert data["relations"][0].get("inverse_name") == "contacts"


# ── validate_relations_definition retourne ValidatedCanonicalManyToManyRelation ─

def test_validate_canonical_m2m_returns_right_type(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    (entities_root / "relations.json").write_text(json.dumps(doc), encoding="utf-8")
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert len(result) == 1
    assert isinstance(result[0], ValidatedCanonicalManyToManyRelation)


def test_validate_canonical_m2m_not_silently_skipped(tmp_path):
    """Une relation canonique M2M n'est jamais silencieusement ignorée."""
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert len(result) == 1


def test_validate_canonical_m2m_from_entity_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].from_entity == "Contact"


def test_validate_canonical_m2m_to_entity_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].to_entity == "Groupe"


def test_validate_canonical_m2m_from_table_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].from_table == "contact"


def test_validate_canonical_m2m_to_table_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].to_table == "groupe"


def test_validate_canonical_m2m_pivot_table_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].pivot_table == "contact_groupe"


def test_validate_canonical_m2m_on_delete_is_sql_form(tmp_path):
    """on_delete est converti en majuscules SQL pour ValidatedCanonicalManyToManyRelation."""
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation(on_delete="cascade"))
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].on_delete == "CASCADE"


def test_validate_canonical_m2m_on_delete_set_null(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation(on_delete="set_null"))
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].on_delete == "SET NULL"


def test_validate_canonical_m2m_on_delete_invalid_raises(tmp_path):
    """on_delete invalide (majuscules ou valeur inconnue) lève EntityRelationsError."""
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation(on_delete="CASCADE"))
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(doc, source="test", entities_root=entities_root)


def test_validate_canonical_m2m_duplicate_pivot_raises(tmp_path):
    """Deux relations partageant la même table pivot lèvent EntityRelationsError."""
    entities_root = _setup_entities(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            _canonical_m2m_relation(name="groupes", pivot_table="contact_groupe"),
            _canonical_m2m_relation(name="groupes2", pivot_table="contact_groupe"),
        ],
    }
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(doc, source="test", entities_root=entities_root)


def test_validate_canonical_m2m_relation_type_attr(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert result[0].relation_type == "many_to_many"


# ── generate_relations_sql produit un CREATE TABLE complet ────────────────────

def test_generate_canonical_m2m_sql_is_create_table(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "CREATE TABLE IF NOT EXISTS contact_groupe" in sql


def test_generate_canonical_m2m_sql_has_auto_increment(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "AUTO_INCREMENT" in sql


def test_generate_canonical_m2m_sql_primary_key_is_id(tmp_path):
    """La PK de la table pivot est id (auto-increment), pas (source_key, target_key)."""
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "PRIMARY KEY (id)" in sql


def test_generate_canonical_m2m_sql_unique_key(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "UNIQUE KEY uq_contact_groupe" in sql


def test_generate_canonical_m2m_sql_foreign_key_from(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "FOREIGN KEY (contact_id)" in sql
    assert "REFERENCES contact (id)" in sql


def test_generate_canonical_m2m_sql_foreign_key_to(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "FOREIGN KEY (groupe_id)" in sql
    assert "REFERENCES groupe (id)" in sql


def test_generate_canonical_m2m_sql_on_delete_cascade(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation(on_delete="cascade"))
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "ON DELETE CASCADE" in sql


def test_generate_canonical_m2m_sql_on_delete_restrict(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation(on_delete="restrict"))
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "ON DELETE RESTRICT" in sql


def test_generate_canonical_m2m_sql_indexes(tmp_path):
    entities_root = _setup_entities(tmp_path)
    doc = _relations_document(_canonical_m2m_relation())
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    sql = generate_relations_sql(result)
    assert "INDEX idx_contact_groupe_contact_id" in sql
    assert "INDEX idx_contact_groupe_groupe_id" in sql


# ── Support legacy M2M refusé ─────────────────────────────────────────────────

def _legacy_m2m_doc() -> dict:
    return {
        "format_version": 1,
        "relations": [
            {
                "type": "many_to_many",
                "source": "contact",
                "target": "groupe",
                "pivot_table": "contact_groupe",
                "source_key": "contact_id",
                "target_key": "groupe_id",
            }
        ],
    }


def test_legacy_m2m_format_version_is_rejected(tmp_path):
    """Le format legacy (format_version: 1) est refusé avec EntityRelationsError."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(_legacy_m2m_doc(), source="test", entities_root=entities_root)
    assert "format_version" in str(exc_info.value)


def test_legacy_m2m_rejection_message_mentions_schema_version(tmp_path):
    """Le message d'erreur invite à utiliser schema_version: 1.0."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(_legacy_m2m_doc(), source="test", entities_root=entities_root)
    assert 'schema_version' in str(exc_info.value)
