"""FK-DDL-REAL-SERVER-001 (SQL Server) — le DDL *généré* s'exécute-t-il ?

Miroir SQL Server de `test_generated_ddl_fk_real_server_pg_001`. Même angle
mort comblé : les tests d'intégration existants écrivent leur DDL à la main
et ne passent jamais par le générateur.

Le bug `FK-IDENTITY-STORAGE-TYPE-001` était ici plus brutal que sur
PostgreSQL. La colonne de clé étrangère étant typée `BIGINT IDENTITY(1,1)`,
le `CREATE TABLE` était purement **refusé** par le serveur :

    Multiple identity columns specified for table. Only one identity column
    per table is allowed.

Autrement dit, `make:relation many_to_one` produisait du SQL inexécutable
sur SQL Server. Vérifié sur SQL Server 2022 (RTM-CU26).

La chaîne exercée est celle de `build:model` :
`normalize_canonical_entity_for_model_build`, `validate_entity_definition`,
`build_entity_sql`.

Marqué `db` + `db_mssql` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_MSSQL=1. Les noms de tables sont générés (uuid), jamais
d'entrée utilisateur dans le DDL.
"""
from __future__ import annotations

import uuid
from typing import Any

import pytest

from core.database import db

pytestmark = [pytest.mark.db, pytest.mark.db_mssql]

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


def test_le_ddl_genere_est_accepte_par_le_serveur(real_mssql_db: None) -> None:
    """Avant le correctif, ce CREATE TABLE était refusé (deux colonnes IDENTITY)."""
    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        rows = db.fetch_all(
            "SELECT COUNT(*) AS n FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?",
            [table],
        )
        assert rows[0]["n"] == 1, f"table {table} non creee"
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_colonne_fk_generee_nest_pas_identity(real_mssql_db: None) -> None:
    """Une seule colonne IDENTITY attendue : la clé primaire."""
    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        rows = db.fetch_all(
            "SELECT c.name AS col, c.is_identity AS ident FROM sys.columns c "
            "WHERE c.object_id = OBJECT_ID(?)",
            [table],
        )
        identity_cols = sorted(r["col"] for r in rows if r["ident"])
        assert identity_cols == ["Id"], (
            f"colonnes IDENTITY attendues ['Id'], obtenues {identity_cols} : "
            "une cle etrangere ne doit pas s'auto-alimenter."
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_colonne_fk_generee_na_pas_de_valeur_par_defaut(real_mssql_db: None) -> None:
    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        rows = db.fetch_all(
            "SELECT COLUMN_DEFAULT AS dflt FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = ? AND COLUMN_NAME = ?",
            [table, "parent_id"],
        )
        assert rows, f"colonne parent_id absente de {table}"
        assert rows[0]["dflt"] is None, (
            f"la colonne de cle etrangere porte DEFAULT {rows[0]['dflt']!r}."
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_insert_omettant_la_fk_requise_est_refuse(real_mssql_db: None) -> None:
    """Le symptôme métier : une FK obligatoire ne doit jamais être inventée."""
    import pyodbc

    table = f"forge_it_fk_child_{_suffix()}"
    db.execute(_generated_ddl(table))
    try:
        with pytest.raises(pyodbc.Error):
            db.execute(f"INSERT INTO {table} DEFAULT VALUES")
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_ddl_genere_ne_porte_aucun_marqueur_sur_la_fk(real_mssql_db: None) -> None:
    """Garde-fou textuel, lisible dans le rapport d'echec."""
    table = f"forge_it_fk_child_{_suffix()}"
    ddl = _generated_ddl(table)
    fk_line = next((line for line in ddl.splitlines() if "parent_id" in line), "")
    assert fk_line, f"ligne parent_id introuvable dans le DDL genere :\n{ddl}"
    present = [m for m in AUTO_GENERATED_MARKERS if m in fk_line.upper()]
    assert not present, (
        f"la colonne de cle etrangere est declaree {fk_line.strip()!r} et porte "
        f"{present} :\n{ddl}"
    )
