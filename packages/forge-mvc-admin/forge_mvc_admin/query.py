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

from core.database.timestamps import utc_now
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


#: Caractère d'échappement du `LIKE`, déclaré par `ESCAPE`.
#:
#: `!` et non `\` : le second est déjà un caractère d'échappement de chaîne sur
#: MariaDB hors `NO_BACKSLASH_ESCAPES`, ce qui rend son comportement dépendant
#: d'un réglage de serveur. `!` n'a de sens pour aucun des quatre.
LIKE_ESCAPE = "!"


def escape_like(value: str) -> str:
    """Neutralise les métacaractères d'un motif `LIKE` saisi par un visiteur.

    Sans cela, chercher `100%` ramènerait tout ce qui commence par `100`, et un
    `_` remplacerait n'importe quel caractère. Ce n'est pas une faille, les
    valeurs partant en paramètres liés, mais un résultat que personne n'a
    demandé.

    Le caractère d'échappement lui même est échappé en premier, sans quoi il
    neutraliserait ce qui le suit.
    """
    for caractere in (LIKE_ESCAPE, "%", "_"):
        value = value.replace(caractere, LIKE_ESCAPE + caractere)
    return value


def build_where_clause(
    resource: AdminResource,
    *,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
) -> "tuple[str, list[Any]]":
    """Clause `WHERE` de la liste, et ses paramètres, dans l'ordre du SQL.

    Rend une chaîne vide et aucun paramètre quand rien n'est demandé.

    Les **noms** de colonnes sont vérifiés contre `filter_fields` et
    `search_fields` de la ressource, jamais contre la seule forme de
    l'identifiant : un nom bien formé mais non déclaré exposerait une colonne
    que la liste n'affiche pas. Les **valeurs** partent en paramètres liés.

    Raises:
        AdminResourceError: une colonne demandée n'est pas déclarée filtrable,
            ou une recherche est demandée sans `search_fields`.
    """
    conditions: list[str] = []
    params: list[Any] = []

    for colonne, valeur in (filters or {}).items():
        if colonne not in resource.filter_fields:
            raise AdminResourceError(
                f"colonne non filtrable : {colonne!r}. "
                f"Déclarées : {', '.join(resource.filter_fields) or 'aucune'}."
            )
        conditions.append(f"{_ident(colonne)} = ?")
        params.append(valeur)

    terme = (search or "").strip()
    if terme:
        if not resource.search_fields:
            raise AdminResourceError(
                f"recherche demandée sur {resource.slug!r}, qui ne déclare "
                "aucun search_fields."
            )
        motif = f"%{escape_like(terme)}%"
        # Un OR par colonne cherchable, parenthésé : sans les parenthèses, le
        # OR absorberait les filtres qui précèdent et les rendrait inopérants.
        ou = " OR ".join(
            f"{_ident(colonne)} LIKE ? ESCAPE '{LIKE_ESCAPE}'"
            for colonne in resource.search_fields
        )
        conditions.append(f"({ou})")
        params.extend([motif] * len(resource.search_fields))

    if not conditions:
        return "", []
    return " WHERE " + " AND ".join(conditions), params


def build_count_sql(
    resource: AdminResource,
    *,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
) -> str:
    """`SELECT COUNT(*) AS total FROM <table>` + la clause de filtre.

    Le compte doit porter sur le **même** ensemble que la liste, sans quoi la
    pagination annoncerait des pages vides.
    """
    where, _ = build_where_clause(resource, filters=filters, search=search)
    return f"SELECT COUNT(*) AS total FROM {_ident(resource.table)}{where}"


def resolve_sort(resource: AdminResource, sort: "str | None") -> str:
    """Colonne de tri demandée, ou celle par défaut de la ressource.

    Le tri porte sur une colonne nommée dans l'URL : elle est vérifiée contre
    `list_fields`, jamais contre la seule forme de l'identifiant. Trier sur une
    colonne non affichée révélerait son ordre, donc une partie de son contenu.

    Raises:
        AdminResourceError: la colonne demandée n'est pas affichée en liste.
    """
    if sort is None or not sort.strip():
        return _order_column(resource)
    demande = sort.strip()
    if demande not in resource.list_fields:
        raise AdminResourceError(
            f"colonne de tri inconnue : {demande!r}. "
            f"Affichées : {', '.join(resource.list_fields)}."
        )
    return demande


def build_list_sql(
    resource: AdminResource,
    *,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
    sort: "str | None" = None,
    descending: bool = False,
) -> str:
    """`SELECT <colonnes> FROM <table>` + filtre, tri et pagination du dialecte.

    La clause de pagination et l'ordre de ses paramètres viennent du backend
    actif : T-SQL ignore `LIMIT` et annonce le décalage en premier. Lire
    `list_params()` pour les valeurs, jamais supposer l'ordre.

    Le tri secondaire sur la clé primaire n'est pas décoratif : deux lignes de
    même valeur triée sortiraient dans un ordre que rien ne garantit, et une
    page paginée en montrerait une deux fois pendant qu'une autre disparaîtrait.

    Il est omis quand le tri porte déjà sur la clé primaire. SQL Server refuse
    une colonne répétée dans un `ORDER BY` (« A column has been specified more
    than once »), là où les trois autres l'acceptent : mesuré contre le serveur,
    pas déduit.
    """
    from core.database.backend import get_backend

    columns = ", ".join(_ident(col) for col in resource.list_fields)
    table = _ident(resource.table)
    colonne_tri = resolve_sort(resource, sort)
    order_by = _ident(colonne_tri)
    sens = "DESC" if descending else "ASC"
    secondaire = "" if colonne_tri == resource.pk else f", {_ident(resource.pk)} ASC"
    where, _ = build_where_clause(resource, filters=filters, search=search)
    return (
        f"SELECT {columns} FROM {table}{where} "
        f"ORDER BY {order_by} {sens}{secondaire}"
        f"{get_backend().dialect.pagination_clause()}"
    )


def list_params(
    *,
    limit: int,
    offset: int,
    resource: "AdminResource | None" = None,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
) -> list[Any]:
    """Paramètres de `build_list_sql()`, dans l'ordre attendu par le dialecte.

    Les paramètres du filtre viennent **en premier**, la clause `WHERE`
    précédant la pagination dans la requête. Les inverser lierait un motif de
    recherche à une borne de page, ce que le serveur refuserait ou, pire,
    accepterait.
    """
    from core.database.backend import get_backend

    avant: list[Any] = []
    if resource is not None:
        _, avant = build_where_clause(resource, filters=filters, search=search)

    values = {"limit": limit, "offset": offset}
    pagination = [values[name] for name in get_backend().dialect.pagination_param_order()]
    return avant + pagination


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
        maintenant = utc_now()
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
        parametres = (*parametres, utc_now())
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


#: Plafond d'une action groupée. Au delà, la requête devient longue et son
#: annulation coûteuse, et une sélection de cette taille vient plus souvent
#: d'un « tout cocher » malencontreux que d'une intention.
BULK_MAX_ROWS = 200


class BulkActionError(ValueError):
    """Sélection refusée pour une action groupée."""


def delete_rows(
    resource: AdminResource,
    execute: Execute,
    *,
    pk_values: "Sequence[Any]",
    max_rows: int = BULK_MAX_ROWS,
) -> int:
    """Supprime plusieurs lignes en une requête (`ADMIN-BULK-ACTIONS-001`).

    Le back-office ne savait supprimer qu'une ligne à la fois : nettoyer deux
    cents inscriptions de test demandait deux cents allers-retours, et deux
    cents confirmations.

    Les identifiants partent en **paramètres liés**, un marqueur par valeur.
    Les concaténer dans la requête serait une injection, et le fait qu'ils
    viennent d'une liste de cases cochées n'y change rien : une case cochée est
    une donnée de requête comme une autre.

    Rend le nombre de lignes réellement supprimées, qui peut être inférieur à
    la sélection : une ligne supprimée entre l'affichage et la validation n'est
    pas une erreur, et refuser toute la fournée pour cela ferait échouer une
    action correcte.

    Raises:
        BulkActionError: sélection vide, ou au delà du plafond.
    """
    valeurs = list(pk_values)
    if not valeurs:
        raise BulkActionError(
            "aucune ligne sélectionnée : une suppression groupée sans "
            "sélection effacerait la table entière si la clause était omise."
        )
    if len(valeurs) > max_rows:
        raise BulkActionError(
            f"{len(valeurs)} lignes sélectionnées, plafond {max_rows}. Une "
            "sélection de cette taille vient plus souvent d'un « tout cocher » "
            "malencontreux que d'une intention."
        )

    marqueurs = ", ".join("?" for _ in valeurs)
    sql = (
        f"DELETE FROM {resource.table} "
        f"WHERE {resource.pk} IN ({marqueurs})"
    )
    return execute(sql, tuple(valeurs))


def count_rows(
    resource: AdminResource,
    fetch_one: FetchOne,
    *,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
) -> int:
    """Nombre de lignes correspondant au filtre, ou de la table entière."""
    _, params = build_where_clause(resource, filters=filters, search=search)
    row = fetch_one(build_count_sql(resource, filters=filters, search=search), tuple(params))
    return int(row["total"]) if row else 0


def list_rows(
    resource: AdminResource,
    fetch_all: FetchAll,
    *,
    limit: int,
    offset: int,
    filters: "dict[str, Any] | None" = None,
    search: "str | None" = None,
    sort: "str | None" = None,
    descending: bool = False,
) -> list[dict[str, Any]]:
    """Page de lignes (colonnes = `list_fields`), filtrée, triée et bornée."""
    return fetch_all(
        build_list_sql(
            resource, filters=filters, search=search, sort=sort, descending=descending
        ),
        tuple(list_params(
            limit=limit, offset=offset, resource=resource, filters=filters, search=search
        )),
    )
