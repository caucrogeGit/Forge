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
