"""CRUD-RELATION-FK-PERSISTED-001 (FORGE-12+, intégration CRUD).

Quand une relation `many_to_one` porte sa colonne FK (non déclarée comme champ
d'entité), `make:crud` injecte un champ synthétique afin que la FK soit :

- persistée par le modèle (colonne présente dans INSERT et UPDATE) ;
- saisissable dans le formulaire via un `RelationField` (select de l'entité liée).

Sans cette injection, le `<select>` s'afficherait mais la valeur choisie ne serait
jamais écrite en base (colonne absente de l'INSERT/UPDATE).
"""
from __future__ import annotations

import json
from pathlib import Path

from cli.entities.canonical_model_normalizer import normalize_canonical_entity_for_model_build
from cli.entities.crud.form_builder import build_form
from cli.entities.crud.model_builder import build_model
from cli.entities.crud.relations_loader import _load_crud_many_to_one_relations
from cli.entities.make_crud import _inject_relation_fk_fields
from cli.entities.validation import validate_entity_definition


def _project(tmp_path: Path) -> Path:
    ents = tmp_path / "mvc" / "entities"
    for name, table, fields in [
        ("AnneeScolaire", "annee_scolaire", [{"name": "libelle", "type": "string", "max_length": 50, "required": True}]),
        ("Classe", "classe", [{"name": "code", "type": "string", "max_length": 50, "required": True}]),
    ]:
        d = ents / name.lower()
        d.mkdir(parents=True)
        (d / f"{name.lower()}.json").write_text(
            json.dumps({"schema_version": "1.0", "name": name, "table": table, "fields": fields}),
            encoding="utf-8",
        )
    (ents / "relations.json").write_text(
        json.dumps({"schema_version": "1.0", "relations": [{
            "type": "many_to_one", "from": "Classe", "to": "AnneeScolaire",
            "name": "annee_scolaire", "foreign_key": "annee_scolaire_id",
            "on_delete": "restrict", "nullable": True, "index": True,
        }]}),
        encoding="utf-8",
    )
    return ents


def _classe_crud(tmp_path: Path):
    ents = _project(tmp_path)
    raw = json.loads((ents / "classe" / "classe.json").read_text(encoding="utf-8"))
    definition = validate_entity_definition(normalize_canonical_entity_for_model_build(raw), source="classe")
    relations = _load_crud_many_to_one_relations(definition, ents)
    _inject_relation_fk_fields(definition, relations)
    model = build_model(definition, relations)
    form, _ = build_form(definition, relations)
    return model, form


def test_fk_persisted_in_insert(tmp_path):
    model, _ = _classe_crud(tmp_path)
    assert 'INSERT INTO classe (Code, annee_scolaire_id)' in model


def test_fk_persisted_in_update(tmp_path):
    model, _ = _classe_crud(tmp_path)
    assert "annee_scolaire_id = ?" in model
    assert "UPDATE classe SET" in model


def test_fk_rendered_as_relation_select_in_form(tmp_path):
    _, form = _classe_crud(tmp_path)
    assert "annee_scolaire_id = RelationField(" in form
    assert 'target="AnneeScolaire"' in form


def test_fk_select_label_strips_id_suffix(tmp_path):
    # Le select porte sur l'entité liée : le libellé retire le suffixe `_id`.
    _, form = _classe_crud(tmp_path)
    assert 'RelationField(label="Annee scolaire"' in form
    assert "Annee scolaire id" not in form


def test_injection_is_idempotent_and_skips_declared_field(tmp_path):
    # Un second passage n'ajoute pas de doublon (le champ existe déjà).
    ents = _project(tmp_path)
    raw = json.loads((ents / "classe" / "classe.json").read_text(encoding="utf-8"))
    definition = validate_entity_definition(normalize_canonical_entity_for_model_build(raw), source="classe")
    relations = _load_crud_many_to_one_relations(definition, ents)
    _inject_relation_fk_fields(definition, relations)
    _inject_relation_fk_fields(definition, relations)
    fk_fields = [f for f in definition["fields"] if f["name"] == "annee_scolaire_id"]
    assert len(fk_fields) == 1
