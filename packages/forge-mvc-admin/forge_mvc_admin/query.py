# pyright: strict
"""Construction de la requête de liste d'une ressource admin (ADMIN-LIST-VIEW-001).

SELECT contraint : seuls des **identifiants** déclarés dans l'`AdminResource`
(table, colonnes, colonne de tri) entrent dans le SQL, et chacun est revalidé en
liste blanche (`_ident`) avant interpolation ; les valeurs (pagination) passent
par des paramètres `?`. Aucune introspection, pas d'ORM, pas de SQL fourni par
l'utilisateur. Précédent : la liste blanche du `group_by` de forge-mvc-stats.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any

from forge_mvc_admin.exceptions import AdminResourceError
from forge_mvc_admin.resources import AdminResource

FetchAll = Callable[[str, Sequence[Any]], list[dict[str, Any]]]
FetchOne = Callable[[str, Sequence[Any]], "dict[str, Any] | None"]
Insert = Callable[[str, Sequence[Any]], int]
Execute = Callable[[str, Sequence[Any]], int]

# Identifiant SQL sûr : minuscules, chiffres, underscores, commençant par une lettre.
_IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def _ident(name: str) -> str:
    """Garde-fou : retourne `name` s'il est un identifiant SQL sûr, sinon lève.

    Les valeurs viennent d'un `AdminResource` déjà validé ; cette revalidation
    rend le SQL interpolé sûr même lu isolément (défense en profondeur).
    """
    if not _IDENT_RE.match(name):
        raise AdminResourceError(f"identifiant SQL invalide : {name!r}")
    return name


def _order_column(resource: AdminResource) -> str:
    return resource.order_by or resource.list_fields[0]


def build_count_sql(resource: AdminResource) -> str:
    """`SELECT COUNT(*) AS total FROM <table>`."""
    return f"SELECT COUNT(*) AS total FROM {_ident(resource.table)}"


def build_list_sql(resource: AdminResource) -> str:
    """`SELECT <colonnes> FROM <table> ORDER BY <tri> ASC LIMIT ? OFFSET ?`."""
    columns = ", ".join(_ident(col) for col in resource.list_fields)
    table = _ident(resource.table)
    order_by = _ident(_order_column(resource))
    return (
        f"SELECT {columns} FROM {table} "
        f"ORDER BY {order_by} ASC LIMIT ? OFFSET ?"
    )


def detail_columns(resource: AdminResource) -> tuple[str, ...]:
    """Colonnes affichées en détail : pk, puis list_fields, puis form_fields (uniques)."""
    ordered: list[str] = []
    for column in (resource.pk, *resource.list_fields, *resource.form_fields):
        if column not in ordered:
            ordered.append(column)
    return tuple(ordered)


def build_get_sql(resource: AdminResource) -> str:
    """`SELECT <colonnes> FROM <table> WHERE <pk> = ? LIMIT 1`."""
    columns = ", ".join(_ident(col) for col in detail_columns(resource))
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"SELECT {columns} FROM {table} WHERE {pk} = ? LIMIT 1"


def get_row(
    resource: AdminResource,
    fetch_one: FetchOne,
    *,
    pk_value: Any,
) -> "dict[str, Any] | None":
    """Retourne la ligne dont la clé primaire vaut `pk_value`, ou None."""
    return fetch_one(build_get_sql(resource), (pk_value,))


def build_insert_sql(resource: AdminResource) -> str:
    """`INSERT INTO <table> (<form_fields>) VALUES (?, …)`."""
    columns = [_ident(col) for col in resource.form_fields]
    table = _ident(resource.table)
    placeholders = ", ".join("?" for _ in columns)
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"


def insert_row(
    resource: AdminResource,
    insert: Insert,
    *,
    values: Sequence[Any],
) -> int:
    """Insère une ligne (valeurs dans l'ordre de `form_fields`). Retourne lastrowid."""
    return insert(build_insert_sql(resource), tuple(values))


def build_update_sql(resource: AdminResource) -> str:
    """`UPDATE <table> SET <form_fields = ?> WHERE <pk> = ? LIMIT 1`."""
    assignments = ", ".join(f"{_ident(col)} = ?" for col in resource.form_fields)
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"UPDATE {table} SET {assignments} WHERE {pk} = ? LIMIT 1"


def update_row(
    resource: AdminResource,
    execute: Execute,
    *,
    values: Sequence[Any],
    pk_value: Any,
) -> int:
    """Met à jour la ligne `pk_value` (valeurs dans l'ordre de `form_fields`).

    Retourne le nombre de lignes affectées (0 si la clé n'existe pas).
    """
    return execute(build_update_sql(resource), (*tuple(values), pk_value))


def build_delete_sql(resource: AdminResource) -> str:
    """`DELETE FROM <table> WHERE <pk> = ? LIMIT 1`."""
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"DELETE FROM {table} WHERE {pk} = ? LIMIT 1"


def delete_row(
    resource: AdminResource,
    execute: Execute,
    *,
    pk_value: Any,
) -> int:
    """Supprime la ligne `pk_value`. Retourne le nombre de lignes affectées (0 si absente)."""
    return execute(build_delete_sql(resource), (pk_value,))


def count_rows(resource: AdminResource, fetch_one: FetchOne) -> int:
    """Nombre total de lignes de la table de la ressource."""
    row = fetch_one(build_count_sql(resource), ())
    return int(row["total"]) if row else 0


def list_rows(
    resource: AdminResource,
    fetch_all: FetchAll,
    *,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    """Page de lignes de la table (colonnes = `list_fields`), triée et bornée."""
    return fetch_all(build_list_sql(resource), (limit, offset))
