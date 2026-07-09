"""FOREIGN-KEY-FIELD-TYPE-001 (ADR-069, retour-013).

La clé étrangère devient un **champ de première classe** de l'entité source :
type `foreign_key` + `references`. Le normaliseur le résout au type de la PK visée
(`identity_type()`, BIGINT UNSIGNED sur MariaDB) avec une colonne snake_case fidèle
au dictionnaire. `make:relation` injecte ce champ dans le JSON de l'entité source.
"""
from __future__ import annotations

import json
from pathlib import Path

from forge_mvc_entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
from forge_mvc_entities.make_relation import _inject_fk_field_into_entity
from forge_mvc_entities.relations import generate_relations_sql, validate_relations_definition


def _entity(name: str, table: str, fields: list[dict]) -> dict:
    return {"schema_version": "1.0", "name": name, "table": table, "fields": fields}


# ── Normalisation du type foreign_key ────────────────────────────────────────

def test_foreign_key_normalise_vers_type_pk_et_colonne_snake():
    norm = normalize_canonical_entity_for_model_build(_entity(
        "Classe", "classe",
        [{"name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire", "required": True}],
    ))
    fk = next(f for f in norm["fields"] if f["name"] == "annee_scolaire_id")
    assert fk["column"] == "annee_scolaire_id"        # snake_case, pas PascalCase
    assert fk["sql_type"] == "BIGINT UNSIGNED"        # type de la PK visée
    assert fk["python_type"] == "int"
    assert fk["nullable"] is False                    # required -> NOT NULL
    assert fk["references"] == "AnneeScolaire"         # métadonnée conservée


def test_foreign_key_nullable_par_defaut():
    norm = normalize_canonical_entity_for_model_build(_entity(
        "Classe", "classe",
        [{"name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire"}],
    ))
    fk = next(f for f in norm["fields"] if f["name"] == "annee_scolaire_id")
    assert fk["nullable"] is True


# ── Injection par make:relation ──────────────────────────────────────────────

def _classe_only(tmp_path: Path) -> Path:
    ents = tmp_path / "mvc" / "entities"
    d = ents / "classe"
    d.mkdir(parents=True)
    (d / "classe.json").write_text(json.dumps(_entity(
        "Classe", "classe", [{"name": "code", "type": "string", "max_length": 30, "required": True}])),
        encoding="utf-8")
    return ents


def test_make_relation_injecte_le_champ_fk(tmp_path):
    ents = _classe_only(tmp_path)
    modified = _inject_fk_field_into_entity(ents, "Classe", "annee_scolaire_id", "AnneeScolaire", nullable=False)
    assert modified is not None
    data = json.loads((ents / "classe" / "classe.json").read_text(encoding="utf-8"))
    fk = next(f for f in data["fields"] if f["name"] == "annee_scolaire_id")
    assert fk == {"name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire", "required": True}


def test_injection_fk_idempotente_et_preserve(tmp_path):
    ents = _classe_only(tmp_path)
    _inject_fk_field_into_entity(ents, "Classe", "annee_scolaire_id", "AnneeScolaire", nullable=True)
    second = _inject_fk_field_into_entity(ents, "Classe", "annee_scolaire_id", "AnneeScolaire", nullable=True)
    data = json.loads((ents / "classe" / "classe.json").read_text(encoding="utf-8"))
    assert second is None  # déjà présent
    assert sum(1 for f in data["fields"] if f["name"] == "annee_scolaire_id") == 1
    assert any(f["name"] == "code" for f in data["fields"])  # champ existant préservé


# ── Bout en bout : FK déclarée -> relations.sql contrainte seule ─────────────

def test_fk_declaree_relations_sql_contrainte_seule(tmp_path):
    ents = tmp_path / "mvc" / "entities"
    for name, table, fields in [
        ("AnneeScolaire", "annee_scolaire", [{"name": "libelle", "type": "string", "max_length": 50, "required": True}]),
        ("Classe", "classe", [
            {"name": "code", "type": "string", "max_length": 30, "required": True},
            {"name": "annee_scolaire_id", "type": "foreign_key", "references": "AnneeScolaire", "required": True},
        ]),
    ]:
        d = ents / name.lower()
        d.mkdir(parents=True)
        (d / f"{name.lower()}.json").write_text(json.dumps(_entity(name, table, fields)), encoding="utf-8")
    (ents / "relations.json").write_text(json.dumps({"schema_version": "1.0", "relations": [
        {"type": "many_to_one", "from": "Classe", "to": "AnneeScolaire", "name": "annee_scolaire",
         "foreign_key": "annee_scolaire_id", "on_delete": "restrict", "nullable": False}]}), encoding="utf-8")
    validated = validate_relations_definition(
        json.loads((ents / "relations.json").read_text(encoding="utf-8")),
        source="r", entities_root=ents)
    sql = generate_relations_sql(validated)
    assert "ADD COLUMN" not in sql                    # la colonne vient de l'entité
    assert "FOREIGN KEY (annee_scolaire_id)" in sql   # relations.sql ne pose que la contrainte
