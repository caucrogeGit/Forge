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
from datetime import datetime, timezone
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
    if not _IDENT_RE.fullmatch(name):
        raise AdminResourceError(f"identifiant SQL invalide : {name!r}")
    return name


def _order_column(resource: AdminResource) -> str:
    return resource.order_by or resource.list_fields[0]


def build_count_sql(resource: AdminResource) -> str:
    """`SELECT COUNT(*) AS total FROM <table>`."""
    return f"SELECT COUNT(*) AS total FROM {_ident(resource.table)}"


def build_list_sql(resource: AdminResource) -> str:
    """`SELECT <colonnes> FROM <table> ORDER BY <tri> ASC` + pagination du dialecte.

    La clause de pagination et l'ordre de ses paramètres viennent du backend
    actif : T-SQL ignore `LIMIT` et annonce le décalage en premier. Lire
    `list_params()` pour les valeurs, jamais supposer l'ordre.
    """
    from core.database.backend import get_backend

    columns = ", ".join(_ident(col) for col in resource.list_fields)
    table = _ident(resource.table)
    order_by = _ident(_order_column(resource))
    return (
        f"SELECT {columns} FROM {table} "
        f"ORDER BY {order_by} ASC"
        f"{get_backend().dialect.pagination_clause()}"
    )


def list_params(*, limit: int, offset: int) -> list[int]:
    """Paramètres de `build_list_sql()`, dans l'ordre attendu par le dialecte."""
    from core.database.backend import get_backend

    values = {"limit": limit, "offset": offset}
    return [values[name] for name in get_backend().dialect.pagination_param_order()]


def detail_columns(resource: AdminResource) -> tuple[str, ...]:
    """Colonnes affichées en détail : pk, puis list_fields, puis form_fields (uniques)."""
    ordered: list[str] = []
    for column in (resource.pk, *resource.list_fields, *resource.form_fields):
        if column not in ordered:
            ordered.append(column)
    return tuple(ordered)


def build_get_sql(resource: AdminResource) -> str:
    """`SELECT <colonnes> FROM <table> WHERE <pk> = ?`.

    Sans `LIMIT 1` : la clause porte sur la **clé primaire**, donc au plus une
    ligne peut correspondre. Le `LIMIT` n'apportait rien et coûtait la
    portabilité, T-SQL ne le connaissant pas (`ADMIN-JOBS-LIMIT-PORTABLE-001`).
    """
    columns = ", ".join(_ident(col) for col in detail_columns(resource))
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"SELECT {columns} FROM {table} WHERE {pk} = ?"


def get_row(
    resource: AdminResource,
    fetch_one: FetchOne,
    *,
    pk_value: Any,
) -> "dict[str, Any] | None":
    """Retourne la ligne dont la clé primaire vaut `pk_value`, ou None."""
    return fetch_one(build_get_sql(resource), (pk_value,))


def build_insert_sql(resource: AdminResource) -> str:
    """`INSERT INTO <table> (<form_fields>[, created_at, updated_at]) VALUES (?, …)`.

    Les horodatages gérés sont **nommés** quand la ressource les déclare
    (ADR-081, `ADMIN-MANAGED-TIMESTAMPS-001`). Le back-office les ignorait, si
    bien qu'une création échouait sur `NOT NULL` dans toute entité engendrée
    avec `options.timestamps`, sur les quatre backends, l'ADR-081 ayant retiré
    les défauts SQL de ces colonnes.
    """
    columns = [_ident(col) for col in resource.form_fields]
    if resource.timestamps:
        columns += ["created_at", "updated_at"]
    table = _ident(resource.table)
    placeholders = ", ".join("?" for _ in columns)
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"


def insert_row(
    resource: AdminResource,
    insert: Insert,
    *,
    values: Sequence[Any],
) -> int:
    """Insère une ligne (valeurs dans l'ordre de `form_fields`). Retourne lastrowid.

    Les horodatages gérés sont posés **ici, en Python**, jamais par le moteur :
    c'est l'autorité que l'ADR-081 a tranchée, et la même que celle du modèle
    engendré par `make:crud`.
    """
    parametres = tuple(values)
    if resource.timestamps:
        maintenant = datetime.now(timezone.utc)
        parametres = (*parametres, maintenant, maintenant)
    return insert(build_insert_sql(resource), parametres)


def build_update_sql(resource: AdminResource) -> str:
    """`UPDATE <table> SET <form_fields = ?> WHERE <pk> = ?`.

    Sans `LIMIT 1`, et c'est ici plus qu'une simplification : `UPDATE ... LIMIT`
    est une **extension MySQL et MariaDB** que PostgreSQL et SQL Server refusent
    tous les deux. Le back-office ne savait donc pas modifier un enregistrement
    sur la moitié des backends, alors que l'ADR-084 les donne au niveau plein
    (`ADMIN-JOBS-LIMIT-PORTABLE-001`).

    La clause portant sur la clé primaire, au plus une ligne est touchée.
    """
    colonnes = list(resource.form_fields)
    assignments = ", ".join(f"{_ident(col)} = ?" for col in colonnes)
    if resource.timestamps:
        # `updated_at` seul : `created_at` ne se réécrit pas. Sans cela, la
        # modification passait sans erreur mais laissait l'horodatage figé, ce
        # qui est plus discret et plus durable qu'un échec.
        assignments += ", updated_at = ?"
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"UPDATE {table} SET {assignments} WHERE {pk} = ?"


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
    parametres = tuple(values)
    if resource.timestamps:
        parametres = (*parametres, datetime.now(timezone.utc))
    return execute(build_update_sql(resource), (*parametres, pk_value))


def build_delete_sql(resource: AdminResource) -> str:
    """`DELETE FROM <table> WHERE <pk> = ?`.

    Sans `LIMIT 1`, pour la même raison que l'`UPDATE` : `DELETE ... LIMIT` est
    une extension MySQL et MariaDB, refusée par PostgreSQL et SQL Server.
    La clause portant sur la clé primaire, au plus une ligne est supprimée.
    """
    table = _ident(resource.table)
    pk = _ident(resource.pk)
    return f"DELETE FROM {table} WHERE {pk} = ?"


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
    return fetch_all(
        build_list_sql(resource),
        tuple(list_params(limit=limit, offset=offset)),
    )
