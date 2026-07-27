# pyright: strict
"""
core/database/table_ddl.py — Rendu dialectal d'une table d'infrastructure
=========================================================================
Un paquet Forge qui livre sa propre table (sessions, jobs, audit, ...) doit
pouvoir la décrire **une fois** et obtenir le DDL correct pour le backend
actif, au lieu d'écrire du SQL propre à un SGBD.

L'audit `OPTIN-DDL-DIALECT-AUDIT-001` a mesuré le coût de l'absence de ce
rendu : douze fichiers SQL livrés par dix opt-ins, aucun exécutable ailleurs
que sur MariaDB, alors que le contrat `Dialect` couvrait déjà les cinq
constructions en cause.

Le SQL reste **visible** (principe 5) : le rendu produit du texte, que la
commande `<opt-in>:init` écrit dans `mvc/migrations/` où l'auteur le relit
avant de l'appliquer (ADR-071).

Périmètre volontairement étroit : les **tables d'infrastructure** livrées
figées par un paquet. Les entités de l'application ont leur propre chaîne,
`forge_mvc_entities.build_entity_sql`, qui part d'un contrat JSON utilisateur
et gère bien plus (relations, médias, slugs). Les deux rendus partagent le
contrat `Dialect` mais pas leur entrée ; les confondre reviendrait à faire
dépendre les opt-ins du moteur d'entités.
"""
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from core.database.backend import Dialect

__all__ = [
    "Column",
    "Index",
    "UniqueConstraint",
    "ForeignKey",
    "TableDefinition",
    "render_create_table",
    "NO_DEFAULT",
]


class _NoDefault:
    """Sentinelle : « cette colonne n'a pas de DEFAULT »."""

    def __repr__(self) -> str:
        return "NO_DEFAULT"


#: Absence de valeur par défaut, distincte de `DEFAULT NULL`.
NO_DEFAULT = _NoDefault()

# Types Forge acceptés, résolus par le dialecte actif.
_SIMPLE = ("text", "integer", "big_integer", "float", "boolean", "date", "datetime", "json")

# SQL Server ne connaît pas RESTRICT ; NO ACTION en est l'équivalent et il est
# compris par les quatre backends. On normalise plutôt que de laisser passer
# une clause qui casse sur un moteur.
_ON_DELETE_ALIASES = {"RESTRICT": "NO ACTION"}


@dataclass(frozen=True)
class Column:
    """Une colonne, décrite en vocabulaire Forge et non en SQL d'un SGBD."""

    name: str
    #: `string`, `char`, ou l'un des types simples, ou `identity`
    #: (clé primaire auto-incrémentée) ou `identity_ref` (référence vers une
    #: telle clé : type de stockage, jamais auto-incrémenté).
    type: str
    length: "int | None" = None
    nullable: bool = False
    default: Any = NO_DEFAULT
    #: `DEFAULT CURRENT_TIMESTAMP` rendu par le dialecte.
    default_now: bool = False
    #: Ajoute la mise à jour automatique là où le dialecte la connaît. Ailleurs
    #: le dialecte rend le simple DEFAULT : à l'application de tenir l'horloge.
    on_update_now: bool = False
    unique: bool = False


@dataclass(frozen=True)
class Index:
    """Index simple ou composite.

    `columns` accepte un nom seul ou une suite de noms. Le contrat `Dialect`
    reçoit la liste jointe, convention déjà suivie par le rendu du socle auth
    (`cli/security/auth_sql.py`).
    """

    name: str
    columns: "str | Sequence[str]"

    @property
    def column_list(self) -> str:
        if isinstance(self.columns, str):
            return self.columns
        return ", ".join(self.columns)


@dataclass(frozen=True)
class UniqueConstraint:
    """Contrainte d'unicité **nommée**, sur une ou plusieurs colonnes.

    À préférer à `Column(unique=True)` quand le nom compte : pouvoir la
    supprimer par son nom, ou simplement conserver un nom existant. Chaque
    dialecte rend sa forme (`UNIQUE KEY nom (col)` en MariaDB,
    `CONSTRAINT nom UNIQUE (col)` ailleurs ; SQLite omet le nom, qu'il
    n'accepte pas dans une contrainte de table).
    """

    name: str
    columns: "str | Sequence[str]"

    @property
    def column_names(self) -> "list[str]":
        if isinstance(self.columns, str):
            return [self.columns]
        return list(self.columns)


@dataclass(frozen=True)
class ForeignKey:
    column: str
    ref_table: str
    ref_column: str = "id"
    on_delete: str = "NO ACTION"


@dataclass(frozen=True)
class TableDefinition:
    name: str
    columns: Sequence[Column]
    primary_key: Sequence[str]
    indexes: Sequence[Index] = field(default_factory=tuple)
    unique_constraints: Sequence[UniqueConstraint] = field(default_factory=tuple)
    foreign_keys: Sequence[ForeignKey] = field(default_factory=tuple)


def _column_sql_type(column: Column, dialect: Dialect) -> str:
    kind = column.type
    if kind == "identity":
        return dialect.identity_type()
    if kind == "identity_ref":
        return dialect.identity_storage_type()
    if kind == "string":
        if column.length is None:
            raise ValueError(f"Colonne '{column.name}' : `length` est requis pour le type 'string'.")
        return dialect.string_type(column.length)
    if kind == "char":
        if column.length is None:
            raise ValueError(f"Colonne '{column.name}' : `length` est requis pour le type 'char'.")
        return dialect.char_type(column.length)
    if kind in _SIMPLE:
        return dialect.simple_type(kind)
    raise ValueError(f"Colonne '{column.name}' : type Forge inconnu : {kind!r}.")


def _column_lines(table: TableDefinition, dialect: Dialect) -> list[str]:
    lines: list[str] = []
    for column in table.columns:
        if column.type == "identity":
            # La forme exacte dépend du dialecte (AUTO_INCREMENT séparé,
            # BIGSERIAL, IDENTITY(1,1), PK portée par la colonne sur SQLite).
            lines.append(dialect.auto_increment_column_ddl(column.name, dialect.identity_type()))
            continue
        parts = [column.name, _column_sql_type(column, dialect)]
        parts.append("NULL" if column.nullable else "NOT NULL")
        if column.default_now:
            parts.append(dialect.timestamp_default_clause(on_update=column.on_update_now))
        elif column.default is not NO_DEFAULT:
            parts.append(f"DEFAULT {dialect.render_literal(column.default)}")
        if column.unique and dialect.unique_is_column_constraint():
            parts.append("UNIQUE")
        lines.append(" ".join(parts))
    return lines


def render_create_table(table: TableDefinition, dialect: Dialect) -> list[str]:
    """Rend le DDL de `table` pour `dialect`, en instructions séparées.

    Retourne le `CREATE TABLE`, puis les `CREATE INDEX` que le dialecte exige
    hors de la création (PostgreSQL, SQLite, SQL Server ; MariaDB les porte en
    ligne). Les instructions sont à exécuter dans l'ordre rendu.
    """
    body = _column_lines(table, dialect)

    has_identity = any(c.type == "identity" for c in table.columns)
    if table.primary_key and (dialect.emits_separate_primary_key() or not has_identity):
        body.append(f"PRIMARY KEY ({', '.join(table.primary_key)})")

    for column in table.columns:
        if column.unique and not dialect.unique_is_column_constraint():
            body.append(dialect.unique_constraint_ddl(table.name, column.name, column.name))

    for unique in table.unique_constraints:
        body.append(dialect.named_unique(unique.name, unique.column_names))

    for fk in table.foreign_keys:
        on_delete = _ON_DELETE_ALIASES.get(fk.on_delete.upper(), fk.on_delete.upper())
        body.append(
            f"FOREIGN KEY ({fk.column}) REFERENCES {fk.ref_table}({fk.ref_column}) "
            f"ON DELETE {on_delete}"
        )

    if dialect.inline_indexes():
        for index in table.indexes:
            body.append(dialect.index_clause(index.name, index.column_list))

    statements = [
        dialect.create_table_opening(table.name)
        + " (\n"
        + ",\n".join(f"    {line}" for line in body)
        + "\n)"
        + dialect.table_suffix()
        + ";"
    ]
    if not dialect.inline_indexes():
        statements += [
            dialect.create_index_sql(table.name, index.name, index.column_list)
            for index in table.indexes
        ]
    return statements
