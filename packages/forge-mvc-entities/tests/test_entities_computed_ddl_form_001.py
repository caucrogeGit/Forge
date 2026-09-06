"""ENTITIES-COMPUTED-DDL-FORM-001 : un champ calculé n'a ni colonne ni saisie.

Le schéma d'entité le dit sans ambiguïté : « Le champ n'a pas de colonne : il
n'est ni inséré ni mis à jour. L'expression part telle quelle dans le SELECT. »

Deux générateurs sur quatre l'ignoraient. Mesuré avant correction, sur un
contrat déclarant `resume` calculé depuis `titre` :

- la table portait `Resume TEXT NULL`, colonne que rien n'écrit jamais puisque
  l'`INSERT` l'exclut déjà, et que rien ne lit puisque le `SELECT` projette
  l'expression : une colonne morte, toujours nulle, qui laissait croire à un
  stockage ;
- le formulaire exposait un champ `resume` saisissable, et ce que l'utilisateur
  y tapait disparaissait sans message.

Le second est le plus grave : offrir une saisie qu'on jette est pire que ne
rien offrir.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

CONTRAT: dict[str, Any] = {
    "schema_version": "1.0",
    "name": "Seance",
    "table": "seance",
    "fields": [
        {"name": "titre", "type": "string", "max_length": 120, "required": True},
        {"name": "resume", "type": "string", "max_length": 200,
         "computed": "SUBSTR(Titre, 1, 40)"},
    ],
    "options": {"timestamps": True, "soft_delete": True},
}


@pytest.fixture
def definition() -> dict[str, Any]:
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )

    return normalize_canonical_entity_for_model_build(CONTRAT)


class TestLaTable:

    def test_le_champ_calcule_n_a_pas_de_colonne(self, definition: dict[str, Any]) -> None:
        from forge_mvc_entities.make_entity import build_entity_sql

        sql = build_entity_sql(definition)

        assert "Resume" not in sql, f"une colonne morte subsiste :\n{sql}"

    def test_les_autres_colonnes_restent(self, definition: dict[str, Any]) -> None:
        """Exclure le calculé ne doit pas emporter ses voisines."""
        from forge_mvc_entities.make_entity import build_entity_sql

        sql = build_entity_sql(definition)

        for colonne in ("Titre", "CreatedAt", "UpdatedAt", "DeletedAt"):
            assert colonne in sql, f"{colonne} a disparu de la table"


class TestLeFormulaire:

    @staticmethod
    def _code(definition: dict[str, Any]) -> str:
        from forge_mvc_entities.crud.form_builder import build_form

        source, _avertissements = build_form(definition)
        return source

    def test_le_champ_calcule_n_est_pas_saisissable(
        self, definition: dict[str, Any]
    ) -> None:
        """Offrir une saisie que l'INSERT jette est pire que ne rien offrir."""
        assert "resume" not in self._code(definition)

    def test_les_champs_ordinaires_restent_saisissables(
        self, definition: dict[str, Any]
    ) -> None:
        assert "titre" in self._code(definition)


class TestLesLecturesEtEcritures:
    """Ce qui marchait déjà doit continuer : la correction ne prend rien."""

    @staticmethod
    def _modele(definition: dict[str, Any]) -> str:
        from forge_mvc_entities.crud.model_builder import build_model

        return build_model(definition)

    def test_la_lecture_projette_l_expression(self, definition: dict[str, Any]) -> None:
        assert "SUBSTR(Titre, 1, 40)" in self._modele(definition)

    def test_l_ecriture_exclut_le_champ_calcule(self, definition: dict[str, Any]) -> None:
        source = self._modele(definition)
        insertion = next(l for l in source.splitlines() if l.startswith("INSERT"))

        assert "Resume" not in insertion, insertion
