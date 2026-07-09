"""RELATIONS-SOURCE-SCOPED-UNIQUENESS-001 (retour-011, F24 / F25).

Le nom d'une relation (accesseur côté source) et sa clé étrangère (colonne d'une
table) sont propres à l'entité source : leur unicité porte sur `(from, name)` et
`(from, foreign_key)`, pas sur `name` / `foreign_key` seuls. Deux entités qui
référencent la même cible (cas standard des pivots) peuvent donc réutiliser le nom
naturel et une colonne fidèle au dictionnaire. Les tables pivot, elles, restent
globalement uniques (ce sont de vraies tables).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_mvc_entities.make_relation import _ensure_no_obvious_duplicates
from forge_mvc_entities.relations import EntityRelationsError, validate_relations_definition


def _entities(tmp_path: Path, *names_tables: tuple[str, str]) -> Path:
    ents = tmp_path / "mvc" / "entities"
    for name, table in names_tables:
        d = ents / name.lower()
        d.mkdir(parents=True)
        (d / f"{name.lower()}.json").write_text(
            json.dumps({"schema_version": "1.0", "name": name, "table": table,
                        "fields": [{"name": "x", "type": "string", "max_length": 10, "required": True}]}),
            encoding="utf-8",
        )
    return ents


def _m2o(frm: str, name: str, fk: str, to: str = "AnneeScolaire") -> dict:
    return {"type": "many_to_one", "from": frm, "to": to, "name": name,
            "foreign_key": fk, "on_delete": "restrict", "nullable": False}


# ── Validateur partagé ───────────────────────────────────────────────────────

def test_meme_nom_et_fk_sur_sources_differentes_acceptes(tmp_path):
    # F24 + F25 : Classe.annee_scolaire et InscriptionEleve.annee_scolaire coexistent,
    # chacune avec sa colonne annee_scolaire_id (dans sa propre table).
    ents = _entities(tmp_path, ("AnneeScolaire", "annee_scolaire"),
                     ("Classe", "classe"), ("InscriptionEleve", "inscription_eleve"))
    candidate = {"schema_version": "1.0", "relations": [
        _m2o("Classe", "annee_scolaire", "annee_scolaire_id"),
        _m2o("InscriptionEleve", "annee_scolaire", "annee_scolaire_id"),
    ]}
    result = validate_relations_definition(candidate, source="r", entities_root=ents)
    assert len(result) == 2  # aucune n'est rejetée


def test_meme_nom_sur_meme_source_refuse(tmp_path):
    ents = _entities(tmp_path, ("AnneeScolaire", "annee_scolaire"), ("Classe", "classe"))
    candidate = {"schema_version": "1.0", "relations": [
        _m2o("Classe", "annee_scolaire", "annee_scolaire_id"),
        _m2o("Classe", "annee_scolaire", "autre_id"),
    ]}
    with pytest.raises(EntityRelationsError) as exc:
        validate_relations_definition(candidate, source="r", entities_root=ents)
    assert "unique sur Classe" in str(exc.value)  # message qualifié par la source


def test_meme_fk_sur_meme_source_refuse(tmp_path):
    ents = _entities(tmp_path, ("AnneeScolaire", "annee_scolaire"), ("Classe", "classe"))
    candidate = {"schema_version": "1.0", "relations": [
        _m2o("Classe", "annee_scolaire", "annee_scolaire_id"),
        _m2o("Classe", "autre_nom", "annee_scolaire_id"),
    ]}
    with pytest.raises(EntityRelationsError) as exc:
        validate_relations_definition(candidate, source="r", entities_root=ents)
    assert "clé étrangère" in str(exc.value) or "foreign_key" in str(exc.value)


# ── Garde-fou interactif de make:relation ────────────────────────────────────

def test_prompt_guard_accepte_sources_differentes():
    existing = [_m2o("Classe", "annee_scolaire", "annee_scolaire_id")]
    # même nom + même fk mais source différente : ne lève pas.
    _ensure_no_obvious_duplicates(existing, _m2o("InscriptionEleve", "annee_scolaire", "annee_scolaire_id"), source="r")


def test_prompt_guard_refuse_meme_source():
    existing = [_m2o("Classe", "annee_scolaire", "annee_scolaire_id")]
    with pytest.raises(ValueError, match="sur Classe"):
        _ensure_no_obvious_duplicates(existing, _m2o("Classe", "annee_scolaire", "autre_id"), source="r")
