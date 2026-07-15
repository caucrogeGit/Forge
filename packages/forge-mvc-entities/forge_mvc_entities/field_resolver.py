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
        # Clé étrangère de première classe (ADR-069) : même type que la PK visée.
        # Toutes les PK Forge sont `identity_type()` (BIGINT UNSIGNED sur MariaDB),
        # donc une FK vers n'importe quelle entité adopte ce type, backend-agnostique.
        return d.identity_type(), "int"

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
