"""OPTIN-DDL-SESSIONS-DB-001 (SQL Server) — la migration rendue s'exécute.

Pilote du chantier `OPTIN-DDL-DIALECTAL`. Le paquet `forge-mvc-sessions-db`
ne livre plus de `.sql` figé : il déclare sa table une fois et
`forge sessions:init` rend le DDL du backend actif.

Ce garde-fou ferme la boucle sur un vrai serveur : le SQL que la commande
écrirait dans `mvc/migrations/` est exécuté, puis la table est réellement
utilisée (insertion, lecture, concurrence optimiste par la colonne `version`).

Avant ce ticket, le fichier livré portait `ENGINE=InnoDB`, `LONGTEXT` et un
`INDEX` en ligne : il était rejeté par SQL Server dès la première instruction.

Marqué `db` + `db_mssql` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_MSSQL=1.
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.backend import get_backend
from core.database.table_ddl import render_create_table

pytestmark = [pytest.mark.db, pytest.mark.db_mssql]

pytest.importorskip("forge_mvc_sessions_db")


def _rendered_statements(table_name: str) -> list[str]:
    """DDL de la table de sessions, renommée pour ne pas heurter la vraie."""
    from dataclasses import replace

    from forge_mvc_sessions_db.tables import FORGE_SESSIONS

    table = replace(
        FORGE_SESSIONS,
        name=table_name,
        # Un nom par index, et non un nom pour tous : la table en porte deux
        # depuis SESSIONS-DELETE-FOR-USER-001, et les nommer pareil crée un
        # doublon. MariaDB le refuse, PostgreSQL et SQL Server l'ignorent en
        # silence par leur `IF NOT EXISTS`, si bien que le test y passait en
        # ne créant qu'un index sur deux.
        indexes=[
            replace(index, name=f"{table_name}_idx{numero}")
            for numero, index in enumerate(FORGE_SESSIONS.indexes)
        ],
    )
    return render_create_table(table, get_backend().dialect)


def test_migration_rendue_sexecute_et_la_table_est_utilisable(real_mssql_db: None) -> None:
    table = f"forge_it_sess_{uuid.uuid4().hex[:12]}"
    try:
        for statement in _rendered_statements(table):
            db.execute(statement)

        db.execute(
            f"INSERT INTO {table} (session_id, data, expire_at, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ["a" * 64, "{}", "2026-12-31 00:00:00", "2026-01-01 00:00:00", "2026-01-01 00:00:00"],
        )
        row = db.fetch_one(f"SELECT version, data FROM {table} WHERE session_id = ?", ["a" * 64])
        assert row is not None
        assert row["version"] == 0, "le DEFAULT rendu sur `version` n'a pas ete applique"

        # F36 : la concurrence optimiste s'appuie sur la garde WHERE version = ?.
        changed = db.execute(
            f"UPDATE {table} SET data = ?, version = version + 1 "
            "WHERE session_id = ? AND version = ?",
            ["{\"a\":1}", "a" * 64, 0],
        )
        assert changed == 1
        stale = db.execute(
            f"UPDATE {table} SET version = version + 1 WHERE session_id = ? AND version = ?",
            ["a" * 64, 0],
        )
        assert stale == 0, "une ecriture perimee doit etre refusee par la garde de version"
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")
