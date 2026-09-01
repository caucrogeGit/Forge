"""ENTITIES-UNIQUE-COMPOSITE-001 : les index déclarés atteignent enfin le SQL.

Le schéma d'entité **acceptait** une clé `indexes` avec un drapeau `unique`, et
la validation sémantique vérifiait que leurs champs existent. Le normaliseur les
écartait ensuite, avec un commentaire disant que `build:model` ne les supportait
pas encore.

Une contrainte d'unicité composite passait donc la validation sans jamais
atteindre la base. Ce n'est pas une fonctionnalité manquante mais une garantie
annoncée et non tenue, ce qui est pire : l'application croyait ses doublons
impossibles.
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.canonical_model_normalizer import (  # noqa: E402
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.make_entity import build_entity_sql  # noqa: E402


def _contrat(**extra: Any) -> dict[str, Any]:
    contrat: dict[str, Any] = {
        "name": "Inscription",
        "table": "inscriptions",
        "fields": [
            {"name": "eleve_id", "type": "integer"},
            {"name": "session_id", "type": "integer"},
            {"name": "note", "type": "string", "length": 50},
        ],
    }
    contrat.update(extra)
    return contrat


UNIQUE_COMPOSITE = [
    {"name": "uq_inscription", "fields": ["eleve_id", "session_id"], "unique": True}
]


class TestNormalisation:
    def test_un_index_declare_atteint_le_modele(self) -> None:
        """Il s'arrêtait ici, écarté par un commentaire."""
        modele = normalize_canonical_entity_for_model_build(
            _contrat(indexes=UNIQUE_COMPOSITE)
        )
        assert modele["indexes"] == [
            {"name": "uq_inscription", "columns": ["EleveId", "SessionId"], "unique": True}
        ]

    def test_les_champs_deviennent_des_colonnes(self) -> None:
        """Le contrat nomme des champs, la base connaît des colonnes."""
        modele = normalize_canonical_entity_for_model_build(
            _contrat(indexes=[{"name": "idx_note", "fields": ["note"]}])
        )
        assert modele["indexes"][0]["columns"] == ["Note"]

    def test_un_index_sans_unique_n_est_pas_unique(self) -> None:
        modele = normalize_canonical_entity_for_model_build(
            _contrat(indexes=[{"name": "idx_note", "fields": ["note"]}])
        )
        assert modele["indexes"][0]["unique"] is False

    def test_sans_index_declare_la_cle_est_absente(self) -> None:
        """Une clé vide encombrerait le modèle de tous les contrats."""
        assert "indexes" not in normalize_canonical_entity_for_model_build(_contrat())

    def test_un_index_sur_un_champ_inconnu_est_ecarte(self) -> None:
        """La validation sémantique le signale déjà, avec son chemin."""
        modele = normalize_canonical_entity_for_model_build(
            _contrat(indexes=[{"name": "idx_x", "fields": ["jamais_declare"]}])
        )
        assert "indexes" not in modele


class TestRenduSql:
    def _v1(self, indexes: "list[dict[str, Any]]") -> dict[str, Any]:
        return {
            "entity": "Inscription",
            "table": "inscriptions",
            "fields": [
                {"name": "id", "column": "Id", "sql_type": "INTEGER", "python_type": "int",
                 "nullable": False, "primary_key": True, "auto_increment": True},
                {"name": "eleve_id", "column": "EleveId", "sql_type": "INTEGER",
                 "python_type": "int", "nullable": False, "primary_key": False,
                 "auto_increment": False},
                {"name": "session_id", "column": "SessionId", "sql_type": "INTEGER",
                 "python_type": "int", "nullable": False, "primary_key": False,
                 "auto_increment": False},
            ],
            "indexes": indexes,
        }

    def test_la_contrainte_composite_est_rendue(self) -> None:
        sql = build_entity_sql(self._v1(
            [{"name": "uq_inscription", "columns": ["EleveId", "SessionId"], "unique": True}]
        ))
        assert "UNIQUE" in sql
        assert "EleveId, SessionId" in sql

    def test_un_index_simple_est_rendu(self) -> None:
        sql = build_entity_sql(self._v1(
            [{"name": "idx_eleve", "columns": ["EleveId"], "unique": False}]
        ))
        assert "idx_eleve" in sql

    def test_sans_index_le_sql_est_inchange(self) -> None:
        """Rétro-compatibilité : un contrat sans index rend ce qu'il rendait."""
        sql = build_entity_sql(self._v1([]))
        assert "UNIQUE" not in sql
        assert "CREATE INDEX" not in sql

    def test_la_contrainte_est_dans_le_create_table(self) -> None:
        """Une contrainte n'est pas un index : elle vit dans la table."""
        sql = build_entity_sql(self._v1(
            [{"name": "uq_inscription", "columns": ["EleveId", "SessionId"], "unique": True}]
        ))
        # Le suffixe de table varie par dialecte : on découpe sur la parenthèse
        # fermante de la définition, pas sur une chaîne figée.
        fin_table = sql.index("\n)")
        assert "UNIQUE" in sql[:fin_table]


class TestGardeDeRegression:
    def test_le_normaliseur_ne_dit_plus_qu_il_ignore_les_index(self) -> None:
        """Le commentaire disait vrai, et c'était le défaut."""
        from pathlib import Path

        from forge_mvc_entities import canonical_model_normalizer

        source = Path(canonical_model_normalizer.__file__).read_text(encoding="utf-8")
        assert "les index (entity[\"indexes\"]) sont ignorés" not in source.lower()

    def test_la_cle_indexes_est_acceptee_par_la_forme_interne(self) -> None:
        from forge_mvc_entities.validation import ALLOWED_ROOT_KEYS

        assert "indexes" in ALLOWED_ROOT_KEYS
