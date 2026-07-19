# pyright: strict
"""POSTGRES-DDL-001 (ADR-084) — les chemins de génération SQL sont dialectaux en PostgreSQL.

Sous DB_BACKEND=postgres, les chemins de génération (entités via
build_entity_sql, socle Auth/User via render_auth_sql, relations many_to_one
via add_foreign_key_sql) produisent du DDL PostgreSQL idiomatique, sans aucun
idiome MariaDB. Validation critère 4 de la promotion (ADR-084).
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_postgres")
pytest.importorskip("forge_mvc_entities")

from forge_mvc_postgres.dialect import PostgreSQLDialect  # noqa: E402

_MARIADB_IDIOMS = ("ENGINE=", "AUTO_INCREMENT", "UNIQUE KEY", "utf8mb4", "`")


def _build_create_table() -> str:
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )
    from forge_mvc_entities.make_entity import build_entity_sql

    entity: dict[str, Any] = {
        "name": "Contact",
        "table": "contact",
        "fields": [
            {"name": "nom", "type": "string", "max_length": 120, "required": True, "unique": True},
            {"name": "age", "type": "integer"},
            {"name": "actif", "type": "boolean"},
        ],
        "options": {"timestamps": True},
    }
    return build_entity_sql(normalize_canonical_entity_for_model_build(entity))


def test_ddl_entite_postgres_idiomatique(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_BACKEND", "postgres")
    from core.database import backend as backend_module

    backend_module.reset_backend()
    try:
        sql = _build_create_table()
        assert "SERIAL" in sql  # PK auto : SERIAL/BIGSERIAL (séquence implicite)
        for idiom in _MARIADB_IDIOMS:
            assert idiom not in sql, f"idiome MariaDB « {idiom} » dans le DDL PostgreSQL"
    finally:
        backend_module.reset_backend()


@pytest.mark.parametrize("table", ["users", "auth_tokens", "auth_audit_log"])
def test_auth_init_rendu_postgres_sans_idiome_mariadb(table: str) -> None:
    from cli.security.auth_sql import render_auth_sql

    sql = render_auth_sql(table, PostgreSQLDialect())
    assert f"CREATE TABLE IF NOT EXISTS {table}" in sql
    for idiom in _MARIADB_IDIOMS:
        assert idiom not in sql, f"idiome MariaDB « {idiom} » dans {table}.sql"


def test_relation_many_to_one_dialectale() -> None:
    statements = PostgreSQLDialect().add_foreign_key_sql(
        table="livre",
        column="auteur_id",
        sql_type="BIGINT",
        nullable=False,
        ref_table="auteur",
        ref_column="id",
        constraint_name="fk_livre_auteur",
        on_delete="RESTRICT",
        on_update="CASCADE",
        index_name="idx_livre_auteur_id",
        add_column=True,
    )
    joined = "\n".join(statements)
    assert "ALTER TABLE livre" in joined
    assert "ADD COLUMN auteur_id BIGINT NOT NULL" in joined
    assert "FOREIGN KEY (auteur_id)" in joined
    assert "REFERENCES auteur" in joined
    for idiom in _MARIADB_IDIOMS:
        assert idiom not in joined


def test_admin_connection_cible_la_base_de_maintenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """get_admin_connection vise « postgres » par défaut, la base demandée sinon."""
    import sys
    import types

    from forge_mvc_postgres.backend import PostgreSQLBackend

    seen: list[str] = []

    def fake_connect(conninfo: str) -> "Any":
        seen.append(conninfo)
        return types.SimpleNamespace(close=lambda: None, autocommit=False)

    monkeypatch.setitem(sys.modules, "psycopg", types.SimpleNamespace(connect=fake_connect))
    monkeypatch.setenv("DB_ADMIN_LOGIN", "admin")
    monkeypatch.setenv("DB_ADMIN_PWD", "secret")

    backend = PostgreSQLBackend()
    backend.get_admin_connection()
    assert "dbname=postgres" in seen[0]
    assert "user=admin" in seen[0]

    backend.get_admin_connection(database="ventes")
    assert "dbname=ventes" in seen[1]
