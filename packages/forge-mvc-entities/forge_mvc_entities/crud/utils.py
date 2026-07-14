# pyright: strict
# pyright: reportPrivateUsage=false
# pyright: reportUnusedFunction=false
"""Pure field helpers for the CRUD generator."""

from __future__ import annotations
from typing import Any, cast

from forge_mvc_entities.crud.context import CrudManyToOneRelation

# Source unique de _to_snake (principe 11) : re-export depuis validation, qui
# en porte la définition canonique. Les modules CRUD continuent de l'importer
# depuis ce module (`from forge_mvc_entities.crud.utils import _to_snake`).
from forge_mvc_entities.validation import _to_snake as _to_snake  # noqa: F401


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _humanize(name: str) -> str:
    return name.replace("_", " ").capitalize()


def pk_field(definition: dict[str, Any]) -> dict[str, Any]:
    """Retourne le champ clé primaire d'une entité, ou lève si absent.

    API publique du moteur d'entités (ENTITIES-PUBLIC-NAMING-API-001), exposée à
    la racine du paquet pour les générateurs de pages publiques du cœur.
    """
    for f in definition["fields"]:
        if f.get("primary_key"):
            return f
    raise ValueError(f"Aucune clé primaire dans l'entité {definition['entity']!r}")


# Alias interne rétro-compatible : les modules CRUD importent encore ``_pk_field``.
_pk_field = pk_field


def _non_pk_fields(definition: dict[str, Any]) -> list[dict[str, Any]]:
    return [f for f in definition["fields"] if not f.get("primary_key")]


def _is_generated(field: dict[str, Any]) -> bool:
    """Champ auto-généré depuis un champ source (slug avec ``source``).

    Exclu du formulaire et de l'``UPDATE`` (stable à l'édition) mais conservé
    dans l'``INSERT`` — le contrôleur le calcule via ``core.http.slug.slugify`` à la
    création (ADR-017, SLUG-SQL-CRUD-001).
    """
    return bool(field.get("source"))


def _is_managed(field: dict[str, Any]) -> bool:
    """Champ géré par le framework (horodatage ``created_at``/``updated_at``, ADR-081).

    Marqué ``managed`` par le normaliseur depuis ``options.timestamps``. Absent
    du formulaire et de la vue de saisie ; la valeur est posée par le modèle
    (``datetime.now(timezone.utc)`` à l'``INSERT``/``UPDATE``), jamais saisie.
    """
    return bool(field.get("managed"))


def _managed_touches_update(field: dict[str, Any]) -> bool:
    """Vrai si l'horodatage géré est réécrit à chaque ``UPDATE`` (``updated_at``).

    Faux pour un horodatage de création stable (``created_at``), exclu de
    l'``UPDATE`` comme un champ auto-généré.
    """
    return field.get("managed") == "timestamp_updated"


def _is_soft_delete(field: dict[str, Any]) -> bool:
    """Vrai si le champ est la marque de suppression logique (``deleted_at``, ADR-083).

    Marqué ``managed = "soft_delete"`` par le normaliseur depuis
    ``options.soft_delete``. Absent des vues, jamais posé à l'INSERT/UPDATE ; le
    modèle le pose à la suppression (``deleted_at = now``) et filtre les lectures
    sur ``deleted_at IS NULL``.
    """
    return field.get("managed") == "soft_delete"


def _soft_delete_column(definition: dict[str, Any]) -> str | None:
    """Colonne de suppression logique de l'entité, ou ``None`` si absente."""
    for field in definition["fields"]:
        if _is_soft_delete(field):
            return field["column"]
    return None


_FORM_FIELD_CLASS_MAP: dict[str, str] = {
    "string":   "StringField",
    "email":    "EmailField",
    "phone":    "PhoneField",
    "url":      "UrlField",
    "textarea": "TextAreaField",
    "slug":     "SlugField",
    "date":     "DateField",
    "datetime": "DateTimeField",
}
_FORM_FIELD_STR_CONSTRAINTS = {"string", "email", "phone", "url", "textarea", "slug"}
_HTML_TYPE_FROM_FORM_FIELD: dict[str, str] = {
    "email":    "email",
    "phone":    "tel",
    "url":      "url",
    "date":     "date",
    "datetime": "datetime-local",
}


def _is_textarea(f: dict[str, Any]) -> bool:
    if cast("dict[str, Any]", f.get("form") or {}).get("field") == "textarea":
        return True
    sql = f.get("sql_type", "").upper()
    return any(sql.startswith(p) for p in ("TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT"))


def _html_input_type(f: dict[str, Any]) -> str:
    """Déduit le type d'input HTML depuis le champ d'entité."""
    form_field = cast("dict[str, Any]", f.get("form") or {}).get("field")
    if form_field in _HTML_TYPE_FROM_FORM_FIELD:
        return _HTML_TYPE_FROM_FORM_FIELD[form_field]

    fname = f["name"].lower()
    sql = f.get("sql_type", "").upper()
    python_type = f.get("python_type", "str")

    if python_type == "date" or (sql.startswith("DATE") and not sql.startswith("DATETIME")):
        return "date"
    if python_type == "datetime" or sql.startswith("DATETIME") or sql.startswith("TIMESTAMP"):
        return "datetime-local"
    if python_type in ("int", "float"):
        return "number"
    if python_type == "str":
        if any(kw in fname for kw in ("email", "courriel", "mail")):
            return "email"
        if any(kw in fname for kw in ("tel", "phone", "telephone", "portable", "mobile", "gsm", "fax")):
            return "tel"
        if any(kw in fname for kw in ("url", "site", "website", "lien")):
            return "url"
    return "text"


def _text_search_fields(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
) -> list[dict[str, Any]]:
    """Retourne les champs VARCHAR/CHAR/TEXT pertinents pour la recherche LIKE."""
    relation_field_names = set(_relation_by_field(relations))
    out: list[dict[str, Any]] = []
    for f in _non_pk_fields(definition):
        if f["name"] in relation_field_names:
            continue
        sql = f.get("sql_type", "").upper()
        if any(sql.startswith(p) for p in ("VARCHAR", "CHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")):
            out.append(f)
    return out


def _text_label_fields(definition: dict[str, Any]) -> list[dict[str, Any]]:
    """Retourne les champs texte non-PK utilisables comme libelle relationnel."""
    return _text_search_fields(definition)


def _is_bool_sql(sql_type: str) -> bool:
    return sql_type.strip().upper() in {"BOOL", "BOOLEAN"}


def _filter_fields(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
) -> list[dict[str, Any]]:
    relation_field_names = set(_relation_by_field(relations))
    result: list[dict[str, Any]] = []
    for f in _non_pk_fields(definition):
        if f["name"] in relation_field_names:
            result.append(f)
            continue
        if cast("dict[str, Any]", f.get("list") or {}).get("filter") is True:
            result.append(f)
    return result


def _media_form_fields(definition: dict[str, Any]) -> list[dict[str, Any]]:
    """Retourne les entrées media déclarées dans l'entité (field='image' ou 'file')."""
    media = definition.get("media")
    if not isinstance(media, list):
        return []
    result: list[dict[str, Any]] = []
    for e in cast("list[Any]", media):
        if isinstance(e, dict):
            entry = cast("dict[str, Any]", e)
            if entry.get("field") in ("image", "file"):
                result.append(entry)
    return result


def _relation_by_field(relations: list[CrudManyToOneRelation] | None) -> dict[str, CrudManyToOneRelation]:
    return {relation.field_name: relation for relation in relations or []}
