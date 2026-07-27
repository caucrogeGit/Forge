"""OPTIN-DDL-RBAC-INIT-001 (SQL Server) — les tables RBAC s'installent vraiment.

Avant ce ticket, `roles`, `permissions` et `role_permissions` n'avaient aucun
chemin de provisioning : pas de commande d'initialisation, un `sql/rbac.sql`
non livré dans le wheel, et un README renvoyant vers un document inexistant.
`forge auth:init` écrivait pourtant un `user_roles.sql` avec une clé étrangère
vers `roles`.

Ce garde-fou applique les trois migrations rendues, dans l'ordre déclaré, puis
vérifie que le modèle tient : unicité du slug, et cascade réelle depuis `roles`
vers `role_permissions`.

Marqué `db` + `db_mssql` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_MSSQL=1.
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.backend import get_backend
from core.database.errors import UniqueViolationError
from core.database.table_ddl import render_create_table

pytestmark = [pytest.mark.db, pytest.mark.db_mssql]

pytest.importorskip("forge_mvc_rbac")


def _install(suffix: str) -> list[str]:
    """Rend et applique les trois migrations RBAC, tables suffixées."""
    from dataclasses import replace

    from forge_mvc_rbac.tables import MIGRATIONS

    renamed = {"roles": f"roles_{suffix}", "permissions": f"permissions_{suffix}",
               "role_permissions": f"role_permissions_{suffix}"}
    created: list[str] = []
    dialect = get_backend().dialect
    for _filename, table in MIGRATIONS:
        target = replace(
            table,
            name=renamed[table.name],
            indexes=[replace(i, name=f"{i.name}_{suffix}") for i in table.indexes],
            foreign_keys=[replace(fk, ref_table=renamed[fk.ref_table]) for fk in table.foreign_keys],
        )
        for statement in render_create_table(target, dialect):
            db.execute(statement)
        created.append(target.name)
    return created


def test_les_trois_tables_sinstallent_et_le_modele_tient(real_mssql_db: None) -> None:
    suffix = uuid.uuid4().hex[:10]
    created: list[str] = []
    try:
        created = _install(suffix)
        roles, permissions, role_permissions = created

        role_id = db.insert(f"INSERT INTO {roles} (name, slug) VALUES (?, ?)", ["Admin", "admin"])
        perm_id = db.insert(f"INSERT INTO {permissions} (code) VALUES (?)", ["admin.access"])
        db.execute(
            f"INSERT INTO {role_permissions} (role_id, permission_id) VALUES (?, ?)",
            [role_id, perm_id],
        )

        # Le slug est unique : la contrainte rendue est bien active.
        with pytest.raises(UniqueViolationError):
            db.insert(f"INSERT INTO {roles} (name, slug) VALUES (?, ?)", ["Autre", "admin"])

        # ON DELETE CASCADE : supprimer le rôle vide la table de liaison.
        db.execute(f"DELETE FROM {roles} WHERE id = ?", [role_id])
        rows = db.fetch_all(f"SELECT 1 AS n FROM {role_permissions}")
        assert rows == [], "la cascade depuis roles n'a pas ete appliquee"
    finally:
        for table in reversed(created):
            db.execute(f"DROP TABLE IF EXISTS {table}")
