"""Pure field helpers for the CRUD generator."""

from __future__ import annotations

import re

from forge_cli.entities.crud.context import CrudManyToOneRelation


# ── Utilitaires ───────────────────────────────────────────────────────────────

def _to_snake(name: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    value = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", value)
    return value.replace("-", "_").lower()


def _humanize(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _pk_field(definition: dict) -> dict:
    for f in definition["fields"]:
        if f.get("primary_key"):
            return f
    raise ValueError(f"Aucune clé primaire dans l'entité {definition['entity']!r}")


def _non_pk_fields(definition: dict) -> list[dict]:
    return [f for f in definition["fields"] if not f.get("primary_key")]


def _is_generated(field: dict) -> bool:
    """Champ auto-généré depuis un champ source (slug avec ``source``).

    Exclu du formulaire et de l'``UPDATE`` (stable à l'édition) mais conservé
    dans l'``INSERT`` — le contrôleur le calcule via ``core.http.slug.slugify`` à la
    création (ADR-017, SLUG-SQL-CRUD-001).
    """
    return bool(field.get("source"))


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


def _is_textarea(f: dict) -> bool:
    if (f.get("form") or {}).get("field") == "textarea":
        return True
    sql = f.get("sql_type", "").upper()
    return any(sql.startswith(p) for p in ("TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT"))


def _html_input_type(f: dict) -> str:
    """Déduit le type d'input HTML depuis le champ d'entité."""
    form_field = (f.get("form") or {}).get("field")
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
    definition: dict,
    relations: list[CrudManyToOneRelation] | None = None,
) -> list[dict]:
    """Retourne les champs VARCHAR/CHAR/TEXT pertinents pour la recherche LIKE."""
    relation_field_names = set(_relation_by_field(relations))
    out = []
    for f in _non_pk_fields(definition):
        if f["name"] in relation_field_names:
            continue
        sql = f.get("sql_type", "").upper()
        if any(sql.startswith(p) for p in ("VARCHAR", "CHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")):
            out.append(f)
    return out


def _text_label_fields(definition: dict) -> list[dict]:
    """Retourne les champs texte non-PK utilisables comme libelle relationnel."""
    return _text_search_fields(definition)


def _is_bool_sql(sql_type: str) -> bool:
    return sql_type.strip().upper() in {"BOOL", "BOOLEAN"}


def _filter_fields(
    definition: dict,
    relations: list[CrudManyToOneRelation] | None = None,
) -> list[dict]:
    relation_field_names = set(_relation_by_field(relations))
    result = []
    for f in _non_pk_fields(definition):
        if f["name"] in relation_field_names:
            result.append(f)
            continue
        if (f.get("list") or {}).get("filter") is True:
            result.append(f)
    return result


def _media_form_fields(definition: dict) -> list[dict]:
    """Retourne les entrées media déclarées dans l'entité (field='image' ou 'file')."""
    media = definition.get("media") or []
    if not isinstance(media, list):
        return []
    return [e for e in media if isinstance(e, dict) and e.get("field") in ("image", "file")]


def _relation_by_field(relations: list[CrudManyToOneRelation] | None) -> dict[str, CrudManyToOneRelation]:
    return {relation.field_name: relation for relation in relations or []}
