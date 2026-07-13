# pyright: strict
# pyright: reportPrivateUsage=false
"""Form builder for the CRUD generator."""

from __future__ import annotations
from typing import Any, cast

from forge_mvc_entities.crud.context import CrudManyToOneRelation
from forge_mvc_entities.crud.utils import (
    _FORM_FIELD_CLASS_MAP,
    _FORM_FIELD_STR_CONSTRAINTS,
    _humanize,
    _is_generated,
    _is_managed,
    _media_form_fields,
    _non_pk_fields,
    _relation_by_field,
)


# ── Mappage SQL → champ de formulaire ─────────────────────────────────────────

def _form_field_code(
    f: dict[str, Any],
    relations_by_field: dict[str, CrudManyToOneRelation] | None = None,
) -> tuple[str, str | None]:
    """Retourne (code_du_champ, avertissement_ou_None)."""
    relation = (relations_by_field or {}).get(f["name"])
    python_type = f.get("python_type", "")
    nullable = f.get("nullable", False)
    required = not nullable
    constraints = f.get("constraints", {})
    label = _humanize(f["name"])
    form_field = cast("dict[str, Any]", f.get("form") or {}).get("field")

    if relation is not None:
        # Le select porte sur l'entité liée, pas sur un identifiant : on retire le
        # suffixe `_id` du nom de colonne pour le libellé (annee_scolaire_id -> « Annee scolaire »).
        fk_name = f["name"]
        rel_label = _humanize(fk_name[:-3] if fk_name.endswith("_id") else fk_name)
        args = [f'label="{rel_label}"', f'target="{relation.target_entity}"', f"required={required}", f'choices_key="{relation.choices_key}"']
        if nullable:
            args.append("empty_value=None")
        return f'RelationField({", ".join(args)})', None

    req_arg = f"required={required}"

    if form_field is not None:
        cls = _FORM_FIELD_CLASS_MAP[form_field]
        args = [f'label="{label}"', req_arg]
        if form_field in _FORM_FIELD_STR_CONSTRAINTS:
            if "min_length" in constraints:
                args.append(f'min_length={constraints["min_length"]}')
            if "max_length" in constraints:
                args.append(f'max_length={constraints["max_length"]}')
        return f'{cls}({", ".join(args)})', None

    if python_type == "bool":
        return f'BooleanField(label="{label}")', None

    if python_type == "str":
        args = [f'label="{label}"', req_arg]
        if "min_length" in constraints:
            args.append(f'min_length={constraints["min_length"]}')
        if "max_length" in constraints:
            args.append(f'max_length={constraints["max_length"]}')
        return f'StringField({", ".join(args)})', None

    if python_type == "int":
        args = [f'label="{label}"', req_arg]
        if "min_value" in constraints:
            args.append(f'min_value={constraints["min_value"]}')
        if "max_value" in constraints:
            args.append(f'max_value={constraints["max_value"]}')
        return f'IntegerField({", ".join(args)})', None

    if python_type == "float":
        args = [f'label="{label}"', req_arg]
        if "min_value" in constraints:
            args.append(f'min_value={constraints["min_value"]}')
        if "max_value" in constraints:
            args.append(f'max_value={constraints["max_value"]}')
        warn = (
            f'{f["name"]} : {f["sql_type"]} → DecimalField'
            " (cleaned_data retourne Decimal ; convertissez en float si votre entité métier l'exige)"
        )
        return f'DecimalField({", ".join(args)})', warn

    if python_type == "date":
        args = [f'label="{label}"', req_arg]
        return f'DateField({", ".join(args)})', None

    if python_type == "datetime":
        args = [f'label="{label}"', req_arg]
        return f'DateTimeField({", ".join(args)})', None

    args = [f'label="{label}"', req_arg]
    warn = (
        f'{f["name"]} : type SQL "{f["sql_type"]}" non mappé → StringField'
        f' (à personnaliser)'
    )
    return f'StringField({", ".join(args)})', warn


def _form_imports(
    fields: list[dict[str, Any]],
    relations: list[CrudManyToOneRelation] | None = None,
    media_entries: list[dict[str, Any]] | None = None,
) -> str:
    classes: set[str] = set()
    relation_fields = set(_relation_by_field(relations))
    for f in fields:
        if f["name"] in relation_fields:
            classes.add("RelationField")
            continue
        form_field = cast("dict[str, Any]", f.get("form") or {}).get("field")
        if form_field is not None:
            classes.add(_FORM_FIELD_CLASS_MAP[form_field])
            continue
        pt = f.get("python_type", "")
        if pt == "int":
            classes.add("IntegerField")
        elif pt == "float":
            classes.add("DecimalField")
        elif pt == "bool":
            classes.add("BooleanField")
        elif pt == "date":
            classes.add("DateField")
        elif pt == "datetime":
            classes.add("DateTimeField")
        else:
            # str et types non mappés → StringField
            classes.add("StringField")
    for entry in media_entries or []:
        if entry.get("field") == "image":
            classes.add("ImageField")
        elif entry.get("field") == "file":
            classes.add("FileField")
    return ", ".join(sorted(classes))


# ── Générateurs de code ───────────────────────────────────────────────────────

def build_form(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
) -> tuple[str, list[str]]:
    """Retourne (code_python, liste_avertissements)."""
    entity = definition["entity"]
    # Sont absents du formulaire : les champs auto-générés (slug avec source)
    # et les champs gérés par le framework (horodatages managed, ADR-081).
    form_fields = [
        f for f in _non_pk_fields(definition)
        if not _is_generated(f) and not _is_managed(f)
    ]
    relations_by_field = _relation_by_field(relations)
    warnings: list[str] = []
    field_lines: list[str] = []

    for f in form_fields:
        code, warn = _form_field_code(f, relations_by_field)
        if warn:
            warnings.append(warn)
        fname = f["name"]
        field_lines.append(f"    {fname} = {code}")

    media_entries = _media_form_fields(definition)
    for entry in media_entries:
        mname = entry["name"]
        mlabel = entry.get("label") or _humanize(mname)
        mrequired = entry.get("required", False)
        cls = "ImageField" if entry["field"] == "image" else "FileField"
        field_lines.append(f'    {mname} = {cls}(label="{mlabel}", required={mrequired})')

    imports = _form_imports(form_fields, relations, media_entries=media_entries)
    lines: list[str] = [
        f"from core.forms import Form, {imports}",
        "",
        "",
        f"class {entity}Form(Form):",
    ]
    if field_lines:
        lines.extend(field_lines)
    else:
        lines.append("    pass")
    lines.append("")
    return "\n".join(lines), warnings
