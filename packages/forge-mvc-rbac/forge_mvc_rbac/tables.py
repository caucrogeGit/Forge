# pyright: strict
"""Tables RBAC, décrites une fois pour les quatre backends.

Ces trois tables n'avaient aucun chemin de provisioning utilisable : le paquet
n'exposait pas de commande d'initialisation, et son `sql/rbac.sql` n'est pas
livré dans le wheel. Le README renvoyait vers un document inexistant. Un
utilisateur qui installait `forge-mvc-rbac` depuis PyPI ne pouvait donc pas
créer ses tables, alors que `forge auth:init` lui écrivait un `user_roles.sql`
portant une clé étrangère vers `roles` (`OPTIN-DDL-RBAC-INIT-001`).

`forge rbac:init` rend ces déclarations pour le backend installé et les écrit
dans `mvc/migrations/`, où elles restent relisibles avant
`forge migration:apply` (charte §7, ADR-071).

L'ordre des migrations est significatif : `role_permissions` référence `roles`
et `permissions`, elle est donc rendue dans un fichier au horodatage
postérieur.
"""
from __future__ import annotations

from core.database.table_ddl import Column, ForeignKey, Index, TableDefinition

__all__ = ["ROLES", "PERMISSIONS", "ROLE_PERMISSIONS", "MIGRATIONS"]

ROLES = TableDefinition(
    name="roles",
    columns=[
        Column("id", "identity"),
        Column("name", "string", length=100),
        Column("slug", "string", length=100, unique=True),
        Column("description", "text", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
)

PERMISSIONS = TableDefinition(
    name="permissions",
    columns=[
        Column("id", "identity"),
        Column("code", "string", length=150, unique=True),
        Column("label", "string", length=255, nullable=True),
        Column("description", "text", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
)

ROLE_PERMISSIONS = TableDefinition(
    name="role_permissions",
    columns=[
        Column("role_id", "identity_ref"),
        Column("permission_id", "identity_ref"),
    ],
    primary_key=["role_id", "permission_id"],
    indexes=[Index("idx_rp_permission", "permission_id")],
    foreign_keys=[
        ForeignKey("role_id", "roles", "id", on_delete="CASCADE"),
        ForeignKey("permission_id", "permissions", "id", on_delete="CASCADE"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
#: `role_permissions` vient après ses deux tables référencées.
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260727120000_create_roles.sql", ROLES),
    ("20260727120100_create_permissions.sql", PERMISSIONS),
    ("20260727120200_create_role_permissions.sql", ROLE_PERMISSIONS),
]
