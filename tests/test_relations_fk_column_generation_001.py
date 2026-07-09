"""RELATIONS-FK-COLUMN-GENERATION-001 (FORGE-12 / FORGE-13 / FORGE-14).

Garde-fou runtime invisible aux portes statiques : une relation `many_to_one`
dont la FK n'est pas un champ d'entité doit produire un `relations.sql`
**applicable** sur MariaDB. Historiquement `generate_relations_sql` n'émettait
que la contrainte, sans créer la colonne (FORGE-12), avec un nom incohérent
(FORGE-13) et un type incompatible avec la PK `BIGINT UNSIGNED` (FORGE-14).

Le flux officiel : relations.sql porte la colonne FK, au type EXACT de la PK
visée, avec le même nom dans la colonne et la contrainte.
"""
from __future__ import annotations

import json
from pathlib import Path

from forge_mvc_entities.relations import (
    _validate_relation_item_canonical,
    generate_relations_sql,
    validate_relations_definition,
)


def _identity_pk() -> dict[str, object]:
    return {
        "name": "id", "column": "Id", "sql_type": "BIGINT UNSIGNED",
        "python_type": "int", "nullable": False, "primary_key": True,
        "auto_increment": True, "constraints": {},
    }


def _plain_field(name: str, column: str, sql_type: str) -> dict[str, object]:
    return {
        "name": name, "column": column, "sql_type": sql_type, "python_type": "str",
        "nullable": True, "primary_key": False, "auto_increment": False, "constraints": {},
    }


def _entity_map(*, classe_fields: list[dict[str, object]] | None = None) -> dict[str, dict[str, object]]:
    classe = [_identity_pk(), _plain_field("code", "Code", "VARCHAR(50)")]
    classe.extend(classe_fields or [])
    return {
        "AnneeScolaire": {"entity": "AnneeScolaire", "table": "annee_scolaire", "fields": [_identity_pk()]},
        "Classe": {"entity": "Classe", "table": "classe", "fields": classe},
    }


def _relation(*, nullable: bool = True, index: bool = True, on_delete: str = "restrict") -> dict[str, object]:
    return {
        "type": "many_to_one", "from": "Classe", "to": "AnneeScolaire",
        "name": "annee_scolaire", "foreign_key": "annee_scolaire_id",
        "on_delete": on_delete, "nullable": nullable, "index": index,
    }


def _sql(entity_map: dict[str, dict[str, object]], relation: dict[str, object]) -> str:
    issues: list[object] = []
    validated = _validate_relation_item_canonical(relation, 0, entity_map, {}, {}, issues)  # type: ignore[arg-type]
    assert not issues, issues
    assert validated is not None
    return generate_relations_sql([validated])


# ── FK non déclarée : relations.sql porte la colonne ─────────────────────────

def test_fk_column_created_with_target_pk_type():
    # FORGE-12 + FORGE-14 : colonne créée, au type exact de la PK visée.
    sql = _sql(_entity_map(), _relation())
    assert "ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NULL;" in sql


def test_fk_column_name_consistent_between_column_and_constraint():
    # FORGE-13 : un seul nom de colonne, identique dans ADD COLUMN et FOREIGN KEY.
    sql = _sql(_entity_map(), _relation())
    assert "ADD COLUMN annee_scolaire_id" in sql
    assert "FOREIGN KEY (annee_scolaire_id)" in sql
    assert "REFERENCES annee_scolaire (Id)" in sql


def test_add_column_precedes_constraint():
    sql = _sql(_entity_map(), _relation())
    assert sql.index("ADD COLUMN") < sql.index("ADD CONSTRAINT")


def test_index_created_on_fk_column():
    sql = _sql(_entity_map(), _relation(index=True))
    assert "CREATE INDEX idx_classe_annee_scolaire_id ON classe (annee_scolaire_id);" in sql


def test_no_index_when_index_false():
    sql = _sql(_entity_map(), _relation(index=False))
    assert "CREATE INDEX" not in sql


def test_not_null_when_relation_not_nullable():
    sql = _sql(_entity_map(), _relation(nullable=False))
    assert "ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NOT NULL;" in sql


def test_set_null_requires_nullable_fk():
    issues: list[object] = []
    _validate_relation_item_canonical(
        _relation(nullable=False, on_delete="set_null"), 0, _entity_map(), {}, {}, issues,  # type: ignore[arg-type]
    )
    assert any("SET NULL" in i.message for i in issues)  # type: ignore[attr-defined]


# ── FK déjà déclarée comme champ : relations.sql ne pose que la contrainte ────

def test_no_add_column_when_fk_is_declared_field():
    declared = {
        "name": "annee_scolaire_id", "column": "annee_scolaire_id", "sql_type": "BIGINT UNSIGNED",
        "python_type": "int", "nullable": True, "primary_key": False,
        "auto_increment": False, "constraints": {},
    }
    sql = _sql(_entity_map(classe_fields=[declared]), _relation())
    assert "ADD COLUMN" not in sql
    assert "FOREIGN KEY (annee_scolaire_id)" in sql


# ── Chaîne complète : entités canoniques → normaliseur → PK BIGINT UNSIGNED ───

def _write_canonical(root: Path, name: str, table: str, fields: list[dict[str, object]]) -> None:
    d = root / name.lower()
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{name.lower()}.json").write_text(
        json.dumps({"schema_version": "1.0", "name": name, "table": table, "fields": fields}) + "\n",
        encoding="utf-8",
    )


def test_end_to_end_fk_type_matches_normalized_identity_pk(tmp_path):
    # La PK synthétique du normaliseur est BIGINT UNSIGNED ; la colonne FK générée
    # doit reprendre ce type exact, sinon MariaDB refuse la contrainte (errno 150).
    _write_canonical(tmp_path, "AnneeScolaire", "annee_scolaire",
                     [{"name": "libelle", "type": "string", "max_length": 50, "required": True}])
    _write_canonical(tmp_path, "Classe", "classe",
                     [{"name": "code", "type": "string", "max_length": 50, "required": True}])
    candidate = {
        "schema_version": "1.0",
        "relations": [{
            "type": "many_to_one", "from": "Classe", "to": "AnneeScolaire",
            "name": "annee_scolaire", "foreign_key": "annee_scolaire_id",
            "on_delete": "restrict", "nullable": True, "index": True,
        }],
    }
    validated = validate_relations_definition(
        candidate, source=str(tmp_path / "relations.json"), entities_root=tmp_path,
    )
    sql = generate_relations_sql(validated)
    assert "ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NULL;" in sql
    assert "REFERENCES annee_scolaire (Id)" in sql
