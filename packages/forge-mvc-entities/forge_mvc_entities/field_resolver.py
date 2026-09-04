# pyright: strict
"""Résolution des types SQL/Python et colonnes d'un champ canonique
(ENTITY-RESOLVER-001, ADR-086).

Depuis un champ au format canonique (schema_version 1.0) et le dialecte du
backend actif (ADR-054), calcule le nom de colonne SQL, le type SQL de colonne
et le type Python runtime. Ces trois dérivations étaient enfouies dans le pont
`canonical_model_normalizer` (couche de transition vers le dict legacy interne) ;
les exposer comme service partagé permet aux générateurs de lire le canonique
directement, sans matérialiser de dict pivot (ADR-086).

Ce service est la source unique du mapping type Forge vers SQL et Python
(principe 11). Il ne dépend que du contrat `Dialect`, jamais d'un backend
concret : le `python_type` (runtime) est fixé ici, indépendant du SGBD ; le
`sql_type` (colonne) vient du dialecte du backend actif.
"""

from __future__ import annotations

from typing import Any

from core.database.backend import Dialect, get_backend

# Longueur de colonne conservatrice pour un `string` sans max_length.
DEFAULT_STRING_LENGTH = 255

# Longueur de colonne d'un slug URL (ADR-017 D3), alignée avec SlugField.
SLUG_MAX_LENGTH = 180

# Nom de colonne de la clé primaire synthétique des entités canoniques. Toute
# entité Forge a un `id` implicite (le contrat canonique n'exprime pas de PK
# explicite) ; sa colonne est toujours `Id`.
IDENTITY_COLUMN = "Id"

# Type Python (runtime) d'un type Forge simple. Non dialectal : il ne dépend
# pas du SGBD. Le type SQL correspondant, lui, vient du dialecte du backend
# actif (ADR-054), via dialect.simple_type().
SIMPLE_PYTHON_TYPE: dict[str, str] = {
    "text":        "str",
    "integer":     "int",
    "big_integer": "int",
    "float":       "float",
    "boolean":     "bool",
    "date":        "date",
    "datetime":    "datetime",
    "email":       "str",
    "password":    "str",
    "slug":        "str",
    "json":        "str",
}


class CanonicalNormalizationError(ValueError):
    """Type Forge inconnu ou paramètres de type invalides dans un champ canonique."""


def dialect() -> Dialect:
    """Dialecte SQL du backend BDD actif (ADR-054)."""
    return get_backend().dialect


def _column_from_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def column_of(field: dict[str, Any]) -> str:
    """Nom de colonne SQL d'un champ de contrat d'entité (ADR-069, ADR-077).

    Convention canonique, source unique du mapping champ vers colonne :

    - un champ `foreign_key` garde son nom snake_case (`annee_scolaire_id`), en
      cohérence avec la colonne émise par `build:model` ;
    - tout autre champ passe en PascalCase (`user_id` vers `UserId`,
      `nom` vers `Nom`).

    La clé primaire (`Id`) n'est pas un champ de contrat : elle n'est pas
    concernée.
    """
    name = str(field.get("name", ""))
    if str(field.get("type", "")) == "foreign_key":
        return name
    return _column_from_name(name)


def resolve_sql_and_python_type(field: dict[str, Any]) -> tuple[str, str]:
    """(sql_type, python_type) d'un champ canonique, via le dialecte actif.

    Lève `CanonicalNormalizationError` sur un type Forge inconnu ou des
    paramètres invalides (`max_length`, `precision`/`scale`).
    """
    forge_type = str(field.get("type", ""))
    field_name = field.get("name", "?")
    d = dialect()

    if forge_type == "string":
        max_length = field.get("max_length", DEFAULT_STRING_LENGTH)
        if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : max_length doit être un entier positif pour type 'string'."
            )
        return d.string_type(max_length), "str"

    if forge_type == "decimal":
        precision = field.get("precision")
        scale = field.get("scale")
        if precision is None or scale is None:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : precision et scale sont requis pour type 'decimal'."
            )
        return d.decimal_type(precision, scale), "float"

    if forge_type == "foreign_key":
        # Clé étrangère de première classe (ADR-069) : la colonne doit STOCKER
        # une valeur d'identité, pas en générer une. D'où `identity_storage_type()`
        # et non `identity_type()`, qui décrit la forme auto-incrémentée de la PK
        # (BIGSERIAL, IDENTITY) et attacherait une séquence à la FK
        # (FK-IDENTITY-STORAGE-TYPE-001, révision de l'ADR-069).
        return d.identity_storage_type(), "int"

    if forge_type in SIMPLE_PYTHON_TYPE:
        return d.simple_type(forge_type), SIMPLE_PYTHON_TYPE[forge_type]

    raise CanonicalNormalizationError(
        f"Champ '{field_name}' : type Forge inconnu : {forge_type!r}."
    )


def sql_type_of(field: dict[str, Any]) -> str:
    """Type SQL de colonne d'un champ canonique (dialectal)."""
    return resolve_sql_and_python_type(field)[0]


def python_type_of(field: dict[str, Any]) -> str:
    """Type Python runtime d'un champ canonique."""
    return resolve_sql_and_python_type(field)[1]


def nullable_of(field: dict[str, Any]) -> bool:
    """Nullabilité d'un champ canonique (ADR-013).

    Nullable par défaut (True) ; `required: true` a priorité et rend le champ
    non nullable.
    """
    if field.get("required") is True:
        return False
    return bool(field.get("nullable", True))


def unique_of(field: dict[str, Any]) -> bool:
    """Contrainte UNIQUE d'un champ canonique."""
    return bool(field.get("unique", False))


def numeric_constraints_of(field: dict[str, Any]) -> dict[str, Any]:
    """Bornes `min`/`max` canoniques traduites en contraintes de validation.

    N'émet `min_value`/`max_value` que pour un champ de type Python numérique
    (`int`/`float`) ; ignoré sinon.
    """
    python_type = python_type_of(field)
    constraints: dict[str, Any] = {}
    if python_type in ("int", "float"):
        if "min" in field:
            constraints["min_value"] = field["min"]
        if "max" in field:
            constraints["max_value"] = field["max"]
    return constraints


def identity_column() -> str:
    """Colonne de la clé primaire synthétique d'une entité canonique (`Id`)."""
    return IDENTITY_COLUMN


# ── Énumération des champs résolus d'une entité canonique (ADR-086) ────────────
# Une entité canonique n'exprime pas ses champs système : la clé primaire `id`
# est implicite, les horodatages et la marque de suppression logique découlent
# de `options`. resolve_entity_fields() produit la liste ordonnée complète des
# champs résolus (id + champs métier + champs système), source unique consommée
# par les générateurs.


def _identity_field() -> dict[str, Any]:
    """Champ résolu de la clé primaire synthétique `id` (auto-incrément)."""
    return {
        "name": "id",
        "column": IDENTITY_COLUMN,
        "forge_type": "identity",
        "sql_type": dialect().identity_type(),
        "python_type": "int",
        "nullable": False,
        "primary_key": True,
        "auto_increment": True,
        "constraints": {},
        "unique": False,
    }


def _system_datetime_field(
    name: str, *, nullable: bool, managed: str | None = None
) -> dict[str, Any]:
    """Champ résolu d'un horodatage système géré par le framework (ADR-081)."""
    field: dict[str, Any] = {
        "name": name,
        "column": column_of({"name": name}),
        "sql_type": dialect().simple_type("datetime"),
        "python_type": "datetime",
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": {},
        "unique": False,
    }
    # La valeur de `managed` distingue la stabilité à l'édition (created stable,
    # updated réécrit à chaque UPDATE, soft_delete posé à la suppression).
    if managed is not None:
        field["managed"] = managed
    return field


def _resolve_business_field(field: dict[str, Any]) -> dict[str, Any]:
    """Champ métier canonique résolu vers sa forme complète (colonne, types...)."""
    forge_type = field.get("type", "")
    sql_type, python_type = resolve_sql_and_python_type(field)

    resolved: dict[str, Any] = {
        "name": field["name"],
        "column": column_of(field),
        # Type Forge conservé : les générateurs décident d'après la NATURE du
        # champ, jamais d'après un nom de type SQL, qui appartient au dialecte
        # (OPTIN-SQL-TYPE-BRANCHING-001). Va dans le sens de l'ADR-086 : la
        # représentation interne se rapproche du canonique.
        "forge_type": forge_type,
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable_of(field),
        "primary_key": False,
        "auto_increment": False,
        "constraints": numeric_constraints_of(field),
        "unique": unique_of(field),
    }

    # Métadonnée de relation : l'entité cible référencée (contrat complet).
    if forge_type == "foreign_key" and "references" in field:
        resolved["references"] = field["references"]

    # Type slug : widget SlugField + longueur de colonne (ADR-017).
    if forge_type == "slug":
        resolved["form"] = {"field": "slug"}
        resolved["constraints"]["max_length"] = SLUG_MAX_LENGTH
        # Slug auto-généré depuis un champ source (étape B) : propagé tel quel,
        # consommé par le générateur CRUD (form exclu, slugify à la création).
        if "source" in field:
            resolved["source"] = field["source"]

    # Champ calculé : l'expression accompagne le champ jusqu'aux générateurs
    # (`ENTITIES-COMPUTED-CANONICAL-001`). Sans cette ligne, le contrat
    # canonique la portait, le résolveur la laissait tomber, et le champ
    # ressortait en colonne ordinaire : `make:crud` engendrait alors un INSERT
    # et un UPDATE sur une colonne qui devait être en lecture seule. La perte
    # était silencieuse, ce qui est le pire des modes de panne.
    if "computed" in field:
        resolved["computed"] = field["computed"]

    if "default" in field:
        resolved["default"] = field["default"]

    return resolved


def resolve_entity_fields(entity: dict[str, Any]) -> list[dict[str, Any]]:
    """Liste ordonnée des champs résolus d'une entité canonique.

    Composée de la clé primaire synthétique `id`, des champs métier résolus
    (tout champ nommé `id` dans le contrat est ignoré, la PK est toujours
    synthétique), puis des champs système déduits de `options` : horodatages
    (`timestamps`) et suppression logique (`soft_delete`).
    """
    fields: list[dict[str, Any]] = [_identity_field()]

    for field in entity.get("fields", []):
        if field.get("name") == "id":
            continue
        fields.append(_resolve_business_field(field))

    options: dict[str, Any] = entity.get("options") or {}
    if options.get("timestamps"):
        fields.append(_system_datetime_field("created_at", nullable=False, managed="timestamp_created"))
        fields.append(_system_datetime_field("updated_at", nullable=False, managed="timestamp_updated"))
    if options.get("soft_delete"):
        fields.append(_system_datetime_field("deleted_at", nullable=True, managed="soft_delete"))

    return fields


# ── Prédicats de nature, pour les générateurs (OPTIN-SQL-TYPE-BRANCHING-001) ──
# Les générateurs testaient des préfixes de types SQL (`VARCHAR`, `LONGTEXT`...)
# pour décider d'un comportement. Ces préfixes appartiennent au dialecte : sur
# SQL Server, dont les types commencent par `NVARCHAR`, aucune condition n'était
# vraie et la fonctionnalité disparaissait sans la moindre erreur.
#
# Ces prédicats répondent à la même question sur la **nature** du champ, qui ne
# dépend d'aucun SGBD.

#: Types Forge dont la valeur est un texte long : saisie multiligne, non
#: filtrable en liste (une clause d'égalité sur un texte long n'a pas de sens).
_LONG_TEXT_TYPES = frozenset({"text", "json"})


#: Préfixes MariaDB, employés UNIQUEMENT en repli pour un fichier au format
#: legacy V1, que Forge lit encore directement (ADR-012). Ces fichiers ont été
#: écrits à l'époque où MariaDB était le seul backend : leurs types SQL sont
#: donc bien du MariaDB, et le repli est exact pour eux.
_LEGACY_LONG_TEXT_PREFIXES = ("TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")


def is_long_text(field: dict[str, Any]) -> bool:
    """Le champ contient-il un texte long (saisie multiligne) ?

    Répond d'après la **nature** du champ dès que celle-ci est connue, ce qui
    est le cas de tout contrat canonique : le résolveur propage `forge_type`.

    Repli sur le type SQL pour un champ issu d'un fichier legacy V1, qui n'a
    pas de nature déclarée. Ce repli n'est pas une réintroduction du défaut :
    ces fichiers datent de l'époque mono-backend, leurs types SQL sont du
    MariaDB, et le chemin canonique — celui de tous les projets actuels — ne
    l'emprunte jamais.
    """
    forge_type = field.get("forge_type")
    if isinstance(forge_type, str) and forge_type:
        return forge_type in _LONG_TEXT_TYPES
    sql_type = str(field.get("sql_type", "")).upper()
    return any(sql_type.startswith(p) for p in _LEGACY_LONG_TEXT_PREFIXES)


#: Préfixes MariaDB des types textuels, repli legacy (voir `is_long_text`).
_LEGACY_TEXT_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")


def is_text_like(field: dict[str, Any]) -> bool:
    """La valeur du champ est-elle du texte ?

    Sur un champ canonique, s'appuie sur `python_type`, déjà indépendant du
    dialecte : couvre `string`, `text`, `email`, `password`, `slug` et `json`,
    exactement l'ensemble que l'ancien test de préfixes retenait sur MariaDB.

    Repli sur le type SQL pour un champ legacy V1, où il sert aussi de contrôle
    de **cohérence** : un `sql_type` entier associé à un `python_type` textuel
    est une incohérence que le repli continue de signaler.
    """
    if isinstance(field.get("forge_type"), str) and field["forge_type"]:
        return field.get("python_type", "") == "str"
    sql_type = str(field.get("sql_type", "")).upper()
    return any(sql_type.startswith(p) for p in _LEGACY_TEXT_PREFIXES)


def is_list_filterable(field: dict[str, Any]) -> bool:
    """Le champ peut-il servir de filtre de liste (égalité exacte) ?

    Textes courts, entiers et booléens. Un texte long, une date ou un nombre à
    virgule ne s'y prêtent pas, comme le retenait déjà l'ancien test.
    """
    if not (isinstance(field.get("forge_type"), str) and field["forge_type"]):
        # Champ legacy V1 : contrôle inchangé sur le type SQL (voir
        # `is_long_text` pour le pourquoi de ce double régime).
        sql_type = str(field.get("sql_type", "")).upper()
        if sql_type in {"BOOL", "BOOLEAN"}:
            return True
        if any(sql_type.startswith(p) for p in _LEGACY_LONG_TEXT_PREFIXES):
            return False
        return any(
            sql_type.startswith(p)
            for p in ("VARCHAR", "CHAR", "INT", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT")
        )
    python_type = field.get("python_type", "")
    if python_type in {"int", "bool"}:
        return True
    return python_type == "str" and not is_long_text(field)
