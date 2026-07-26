"""FK-DDL-REAL-SERVER-001 — le DDL *généré* s'exécute-t-il correctement ?

Ce fichier ferme un chaînon que rien ne couvrait : « entité canonique →
DDL généré → exécution sur un serveur réel ». Les tests d'intégration
existants (`test_db_backend_integration_pg_001`, son homologue mssql)
écrivent leur DDL **à la main** ; ils valident la couche d'accès, jamais le
générateur. C'est cet angle mort qui a laissé passer
`FK-IDENTITY-STORAGE-TYPE-001` : une colonne de clé étrangère typée
`BIGSERIAL` recevait sa propre séquence, et un INSERT omettant une clé
pourtant NOT NULL était accepté avec une valeur fabriquée.

La chaîne exercée ici est celle de `build:model` :
`normalize_canonical_entity_for_model_build` puis
`validate_entity_definition` puis `build_entity_sql`.

Marqué `db` + `db_pg` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_PG=1. Les noms de tables sont générés (uuid), jamais
d'entrée utilisateur dans le DDL.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest

from core.database import db

pytestmark = [pytest.mark.db, pytest.mark.db_pg]

# Marqueurs d'auto-génération : aucun ne doit toucher une colonne de clé étrangère.
AUTO_GENERATED_MARKERS = ("SERIAL", "IDENTITY", "AUTO_INCREMENT", "AUTOINCREMENT")


def _suffix() -> str:
    return uuid.uuid4().hex[:12]


def _canonical_entity(table: str) -> dict[str, Any]:
    """Entité canonique minimale portant une clé étrangère requise."""
    return {
        "schema_version": "1.0",
        "name": "ItFkChild",
        "table": table,
        "fields": [
            {
                "name": "parent_id",
                "type": "foreign_key",
                "references": "ItFkParent",
                "required": True,
            }
        ],
    }


def _generated_ddl(table: str) -> str:
    """Reproduit la chaîne de `build:model`, sans écrire aucun fichier."""
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )
    from forge_mvc_entities.make_entity import build_entity_sql
    from forge_mvc_entities.validation import validate_entity_definition

    normalized = normalize_canonical_entity_for_model_build(_canonical_entity(table))
    definition = validate_entity_definition(normalized, source="<test>")
    return build_entity_sql(definition)


def test_colonne_fk_generee_na_pas_de_valeur_par_defaut(real_pg_db: None) -> None:
    """La colonne FK ne doit rien fabriquer toute seule.

    Avant FK-IDENTITY-STORAGE-TYPE-001 elle était déclarée BIGSERIAL, donc
    dotée d'un DEFAULT nextval() et d'une séquence dédiée.
    """
    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        rows = db.fetch_all(
            "SELECT column_name, column_default FROM information_schema.columns "
            "WHERE table_name = ? AND column_name = ?",
            [table, "parent_id"],
        )
        assert rows, f"colonne parent_id absente de {table}"
        default = rows[0]["column_default"]
        assert default is None, (
            f"la colonne de cle etrangere parent_id porte DEFAULT {default!r} : "
            "elle se verrait attribuer une valeur sans que l'appelant la fournisse."
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_aucune_sequence_creee_pour_la_colonne_fk(real_pg_db: None) -> None:
    """Une seule séquence attendue : celle de la clé primaire."""
    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        rows = db.fetch_all(
            "SELECT sequencename FROM pg_sequences WHERE schemaname = 'public' "
            "AND sequencename LIKE ?",
            [f"{table}%"],
        )
        names = sorted(r["sequencename"] for r in rows)
        assert not [n for n in names if "parent_id" in n], (
            f"sequence(s) creee(s) pour la cle etrangere : {names}"
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_insert_omettant_la_fk_requise_est_refuse(real_pg_db: None) -> None:
    """Le symptôme métier du bug : une FK obligatoire silencieusement inventée."""
    import psycopg

    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        with pytest.raises(psycopg.Error):
            db.execute(f"INSERT INTO {table} DEFAULT VALUES")
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_ddl_genere_ne_porte_aucun_marqueur_sur_la_fk(real_pg_db: None) -> None:
    """Garde-fou textuel, lisible dans le rapport d'echec."""
    table = f"forge_it_fk_child_{_suffix()}"
    ddl = _generated_ddl(table)
    fk_line = next(
        (line for line in ddl.splitlines() if "parent_id" in line),
        "",
    )
    assert fk_line, f"ligne parent_id introuvable dans le DDL genere :\n{ddl}"
    upper = fk_line.upper()
    present = [m for m in AUTO_GENERATED_MARKERS if m in upper]
    assert not present, (
        f"la colonne de cle etrangere est declaree {fk_line.strip()!r} et porte "
        f"{present} :\n{ddl}"
    )
