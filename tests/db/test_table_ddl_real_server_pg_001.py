"""DB-TABLE-DDL-RENDERER-001 (PostgreSQL) — le DDL rendu s'exécute vraiment.

Le rendu dialectal ne vaut que s'il produit du SQL que le serveur accepte.
Ce garde-fou exécute le DDL rendu pour une table d'infrastructure
représentative (clé primaire textuelle, index, identité auto-incrémentée,
horodatages, clé étrangère), puis vérifie que la table est utilisable.

Marqué `db` + `db_pg` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_PG=1. Noms de tables générés (uuid).
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.backend import get_backend
from core.database.table_ddl import (
    Column,
    ForeignKey,
    Index,
    TableDefinition,
    render_create_table,
)

pytestmark = [pytest.mark.db, pytest.mark.db_pg]


def _suffix() -> str:
    return uuid.uuid4().hex[:12]


def test_table_sans_identite_sexecute_et_accepte_une_ligne(real_pg_db: None) -> None:
    table = f"forge_it_ddl_{_suffix()}"
    definition = TableDefinition(
        name=table,
        columns=[
            Column("session_id", "char", length=64),
            Column("data", "text"),
            Column("expire_at", "datetime"),
            Column("version", "integer", default=0),
        ],
        primary_key=["session_id"],
        indexes=[Index(f"idx_{table}_expire", "expire_at")],
    )
    statements = render_create_table(definition, get_backend().dialect)
    try:
        for statement in statements:
            db.execute(statement)
        db.execute(
            f"INSERT INTO {table} (session_id, data, expire_at) VALUES (?, ?, ?)",
            ["a" * 64, "{}", "2026-01-01 00:00:00"],
        )
        rows = db.fetch_all(f"SELECT version FROM {table}")
        assert rows[0]["version"] == 0, "le DEFAULT rendu n'a pas ete applique"
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_table_avec_identite_horodatages_et_fk(real_pg_db: None) -> None:
    parent = f"forge_it_par_{_suffix()}"
    child = f"forge_it_chi_{_suffix()}"
    parent_def = TableDefinition(
        name=parent,
        columns=[Column("id", "identity"), Column("label", "string", length=100)],
        primary_key=["id"],
    )
    child_def = TableDefinition(
        name=child,
        columns=[
            Column("id", "identity"),
            Column("parent_id", "identity_ref"),
            Column("note", "text", nullable=True),
            Column("created_at", "datetime", default_now=True),
        ],
        primary_key=["id"],
        foreign_keys=[ForeignKey("parent_id", parent, "id", on_delete="RESTRICT")],
    )
    dialect = get_backend().dialect
    try:
        for statement in render_create_table(parent_def, dialect):
            db.execute(statement)
        for statement in render_create_table(child_def, dialect):
            db.execute(statement)
        parent_id = db.insert(f"INSERT INTO {parent} (label) VALUES (?)", ["x"])
        db.insert(f"INSERT INTO {child} (parent_id) VALUES (?)", [parent_id])
        rows = db.fetch_all(f"SELECT created_at FROM {child}")
        assert rows[0]["created_at"] is not None, "l'horodatage par defaut n'a pas ete pose"
        # La contrainte de cle etrangere est reellement active.
        with pytest.raises(Exception):
            db.insert(f"INSERT INTO {child} (parent_id) VALUES (?)", [999999])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {child}")
        db.execute(f"DROP TABLE IF EXISTS {parent}")
