# pyright: strict
"""Instantané de l'état courant vers des fixtures (`FIXTURES-SNAPSHOT-001`).

Écrire des fixtures à la main coûte cher et vieillit mal : une colonne ajoutée
au contrat, et tous les `INSERT` sont à reprendre. La base contient pourtant
déjà un jeu de données cohérent, celui avec lequel on travaille.

Ce module le rend en `INSERT` relisibles, que l'on range dans `mvc/fixtures/`.

## Ce qui rend ce module dangereux, et comment il s'en garde

**Il lit des données réelles.** Sur un environnement de recette alimenté depuis
la production, ces données sont celles de personnes, et le fichier produit
finit dans un dépôt Git, où il ne s'efface plus.

Trois gardes en découlent.

- L'exécution en `APP_ENV=prod` est **refusée** sans `--force`, comme
  `fixtures:load --run` (ADR-074).
- Un plafond de lignes s'applique, et il est bas : une fixture est une amorce,
  pas une sauvegarde. Une table de cent mille lignes n'a rien à faire dans
  `mvc/fixtures/`.
- La sortie est **affichée** par défaut. Écrire un fichier se demande, et un
  fichier existant n'est jamais écrasé sans qu'on le dise (charte §7).

Le module ne choisit **pas** les colonnes à masquer. Il ne sait pas lesquelles
portent une donnée personnelle, et prétendre le deviner donnerait une fausse
assurance : l'exploitant relit ce qui est affiché avant de l'écrire, et c'est
précisément pourquoi la sortie est affichée d'abord.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Protocol

__all__ = [
    "SnapshotError",
    "DEFAULT_LIMIT",
    "MAX_LIMIT",
    "TableSnapshot",
    "render_insert",
    "render_snapshot",
    "snapshot_table",
]

#: Une fixture est une amorce : quelques dizaines de lignes suffisent.
DEFAULT_LIMIT = 50

#: Au delà, ce n'est plus une fixture mais un export, et `mvc/fixtures/` n'est
#: pas l'endroit pour cela.
MAX_LIMIT = 1000

#: Un identifiant SQL simple. Le nom de table vient de la ligne de commande et
#: entre dans une requête : il est vérifié plutôt qu'échappé, aucun backend
#: n'acceptant un nom de table en paramètre lié.
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SnapshotError(ValueError):
    """Table, plafond ou dialecte inexploitables."""


class _Dialect(Protocol):
    def render_literal(self, value: object) -> str: ...
    def limit_clause(self) -> str: ...


class _Db(Protocol):
    def fetch_all(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "list[dict[str, Any]]": ...


@dataclass(frozen=True)
class TableSnapshot:
    """Lignes lues, et si le plafond a coupé."""

    table: str
    columns: "tuple[str, ...]"
    rows: "tuple[dict[str, Any], ...]"
    truncated: bool = False

    @property
    def is_empty(self) -> bool:
        return not self.rows


def _valider_table(name: str) -> str:
    table = (name or "").strip()
    if not _IDENT_RE.fullmatch(table):
        raise SnapshotError(
            f"nom de table invalide : {name!r}. Attendu un identifiant SQL "
            "simple, lettres, chiffres et souligné."
        )
    return table


def snapshot_table(
    table: str,
    *,
    limit: int = DEFAULT_LIMIT,
    order_by: "str | None" = None,
    db: "_Db | None" = None,
    dialect: "_Dialect | None" = None,
) -> TableSnapshot:
    """Lit une table et rend ses lignes.

    Une ligne de plus que le plafond est demandée, pour savoir qu'il en restait
    et le dire, plutôt que de rendre un instantané tronqué qui ressemble à un
    instantané complet.

    Raises:
        SnapshotError: nom de table ou plafond invalides.
    """
    nom = _valider_table(table)
    if not isinstance(limit, int) or isinstance(limit, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise SnapshotError(f"le plafond doit être un entier. Reçu : {limit!r}.")
    if limit < 1:
        raise SnapshotError(f"le plafond doit valoir au moins 1. Reçu : {limit}.")
    if limit > MAX_LIMIT:
        raise SnapshotError(
            f"plafond trop élevé : {limit} dépasse {MAX_LIMIT}. Au delà, ce "
            "n'est plus une fixture mais un export."
        )

    if db is None or dialect is None:
        from core.database import db as module_db
        from core.database.backend import get_backend

        db = db if db is not None else module_db  # pyright: ignore[reportAssignmentType]
        dialect = dialect if dialect is not None else get_backend().dialect

    tri = f" ORDER BY {_valider_table(order_by)}" if order_by else ""
    sql = f"SELECT * FROM {nom}{tri}{dialect.limit_clause()}"
    lignes = db.fetch_all(sql, (limit + 1,))  # pyright: ignore[reportOptionalMemberAccess]

    tronque = len(lignes) > limit
    retenues = tuple(lignes[:limit])
    colonnes = tuple(retenues[0].keys()) if retenues else ()
    return TableSnapshot(nom, colonnes, retenues, tronque)


def render_insert(
    table: str,
    columns: "tuple[str, ...]",
    row: "dict[str, Any]",
    dialect: "_Dialect",
) -> str:
    """Une instruction `INSERT` pour une ligne, littéraux rendus par le dialecte.

    Les valeurs sont des **littéraux** et non des paramètres liés : le fichier
    produit est un artefact relu par un humain avant d'être joué, ce que
    l'ADR-075 réserve précisément à ce cas.
    """
    valeurs = ", ".join(dialect.render_literal(row.get(col)) for col in columns)
    noms = ", ".join(columns)
    return f"INSERT INTO {table} ({noms}) VALUES ({valeurs});"


def render_snapshot(
    snapshot: TableSnapshot, dialect: "_Dialect", *, source: str = "fixtures:snapshot"
) -> str:
    """Fichier de fixtures complet, en-tête compris.

    L'en-tête dit d'où viennent les données et ce qu'elles peuvent contenir. Un
    fichier de fixtures est relu des mois plus tard, souvent par quelqu'un
    d'autre, et rien dans un `INSERT` ne dit qu'il vient d'une base réelle.
    """
    lignes = [
        f"-- Instantané de la table « {snapshot.table} », engendré par {source}.",
        "-- RELISEZ CE FICHIER avant de le versionner : il vient d'une base",
        "-- réelle et peut contenir des données personnelles.",
    ]
    if snapshot.truncated:
        lignes.append(
            "-- INSTANTANÉ TRONQUÉ : la table contenait plus de lignes que le "
            "plafond demandé."
        )
    if snapshot.is_empty:
        lignes.append("-- La table est vide : aucun INSERT à produire.")
        return "\n".join(lignes) + "\n"

    lignes.append("")
    lignes.extend(
        render_insert(snapshot.table, snapshot.columns, ligne, dialect)
        for ligne in snapshot.rows
    )
    return "\n".join(lignes) + "\n"
