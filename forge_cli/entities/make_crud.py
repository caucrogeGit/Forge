"""forge make:crud — génération scaffolding CRUD depuis une entité JSON Forge.

Génère pour une entité donnée :
    mvc/controllers/{snake}_controller.py
    mvc/models/{snake}_model.py
    mvc/forms/{snake}_form.py
    mvc/views/layouts/app.html
    mvc/views/{snake}/index.html
    mvc/views/{snake}/show.html
    mvc/views/{snake}/form.html

Les fichiers existants ne sont jamais écrasés ([PRÉSERVÉ]).
Les routes sont affichées sur stdout, jamais injectées automatiquement.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from forge_cli.entities.validation import (
    EntityDefinitionError,
    validate_entity_definition,
)
import forge_cli.output as out


# ── Résultat ──────────────────────────────────────────────────────────────────

@dataclass
class MakeCrudResult:
    created: list[Path] = dc_field(default_factory=list)
    preserved: list[Path] = dc_field(default_factory=list)
    warnings: list[str] = dc_field(default_factory=list)
    route_block: str = ""
    dry_run: bool = False


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


def _is_textarea(f: dict) -> bool:
    sql = f.get("sql_type", "").upper()
    return any(sql.startswith(p) for p in ("TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT"))


# ── Mappage SQL → champ de formulaire ─────────────────────────────────────────

def _form_field_code(f: dict) -> tuple[str, str | None]:
    """Retourne (code_du_champ, avertissement_ou_None)."""
    python_type = f.get("python_type", "")
    nullable = f.get("nullable", False)
    required = not nullable
    constraints = f.get("constraints", {})
    label = _humanize(f["name"])

    if python_type == "bool":
        return f'BooleanField(label="{label}")', None

    req_arg = f"required={required}"

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
        return f'DecimalField({", ".join(args)})', None

    if python_type in ("date", "datetime"):
        args = [f'label="{label}"', req_arg]
        warn = (
            f'{f["name"]} : {f["sql_type"]} → StringField'
            f' (pas de DateField en V1.0 — à personnaliser)'
        )
        return f'StringField({", ".join(args)})', warn

    args = [f'label="{label}"', req_arg]
    warn = (
        f'{f["name"]} : type SQL "{f["sql_type"]}" non mappé → StringField'
        f' (à personnaliser)'
    )
    return f'StringField({", ".join(args)})', warn


def _form_imports(fields: list[dict]) -> str:
    classes: set[str] = {"StringField"}
    for f in fields:
        pt = f.get("python_type", "")
        if pt == "int":
            classes.add("IntegerField")
        elif pt == "float":
            classes.add("DecimalField")
        elif pt == "bool":
            classes.add("BooleanField")
    return ", ".join(sorted(classes))


# ── Générateurs de code ───────────────────────────────────────────────────────

def build_form(definition: dict) -> tuple[str, list[str]]:
    """Retourne (code_python, liste_avertissements)."""
    entity = definition["entity"]
    non_pk = _non_pk_fields(definition)
    warnings: list[str] = []
    field_lines: list[str] = []

    for f in non_pk:
        code, warn = _form_field_code(f)
        if warn:
            warnings.append(warn)
        fname = f["name"]
        field_lines.append(f"    {fname} = {code}")

    imports = _form_imports(non_pk)
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


def build_model(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    table = definition["table"]
    pk = _pk_field(definition)
    pk_col = pk["column"]
    pk_name = pk["name"]
    non_pk = _non_pk_fields(definition)
    auto_inc = pk.get("auto_increment", False)

    insert_fields = non_pk if auto_inc else definition["fields"]
    insert_cols = ", ".join(f["column"] for f in insert_fields)
    insert_placeholders = ", ".join("?" for _ in insert_fields)
    insert_values = ", ".join(f'data["{f["name"]}"]' for f in insert_fields)
    # Évite (,) ou (, id) qui sont des SyntaxError Python quand il n'y a aucun champ
    insert_exec = (
        f"cursor.execute(INSERT, ({insert_values},))"
        if insert_fields else
        "cursor.execute(INSERT)"
    )

    if non_pk:
        update_set = ", ".join(f'{f["column"]} = ?' for f in non_pk)
        update_values = ", ".join(f'data["{f["name"]}"]' for f in non_pk)
        update_constant = f'"UPDATE {table} SET {update_set} WHERE {pk_col} = ?"'
        update_exec = f"cursor.execute(UPDATE, ({update_values}, {pk_name}))"
    else:
        update_constant = "None  # aucun champ métier — UPDATE non applicable"
        update_exec = "return  # aucun champ à mettre à jour"

    lines: list[str] = [
        "from core.database.connection import get_connection, close_connection",
        "",
        f'SELECT_ALL   = "SELECT * FROM {table} ORDER BY {pk_col}"',
        f'SELECT_BY_ID = "SELECT * FROM {table} WHERE {pk_col} = ?"',
        f'INSERT       = "INSERT INTO {table} ({insert_cols}) VALUES ({insert_placeholders})"',
        f'UPDATE       = {update_constant}',
        f'DELETE       = "DELETE FROM {table} WHERE {pk_col} = ?"',
        "",
        "",
        f"def get_{plural}():",
        "    connection = None",
        "    cursor = None",
        "    try:",
        "        connection = get_connection()",
        "        cursor = connection.cursor(dictionary=True)",
        "        cursor.execute(SELECT_ALL)",
        "        return cursor.fetchall()",
        "    finally:",
        "        if cursor:",
        "            cursor.close()",
        "        close_connection(connection)",
        "",
        "",
        f"def get_{snake}_by_id({pk_name}):",
        "    connection = None",
        "    cursor = None",
        "    try:",
        "        connection = get_connection()",
        "        cursor = connection.cursor(dictionary=True)",
        f"        cursor.execute(SELECT_BY_ID, ({pk_name},))",
        "        return cursor.fetchone()",
        "    finally:",
        "        if cursor:",
        "            cursor.close()",
        "        close_connection(connection)",
        "",
        "",
        f"def add_{snake}(data):",
        "    connection = None",
        "    cursor = None",
        "    try:",
        "        connection = get_connection()",
        "        cursor = connection.cursor()",
        f"        {insert_exec}",
        "        connection.commit()",
        "    finally:",
        "        if cursor:",
        "            cursor.close()",
        "        close_connection(connection)",
        "",
        "",
        f"def update_{snake}({pk_name}, data):",
        "    connection = None",
        "    cursor = None",
        "    try:",
        "        connection = get_connection()",
        "        cursor = connection.cursor()",
        f"        {update_exec}",
        "        connection.commit()",
        "    finally:",
        "        if cursor:",
        "            cursor.close()",
        "        close_connection(connection)",
        "",
        "",
        f"def delete_{snake}({pk_name}):",
        "    connection = None",
        "    cursor = None",
        "    try:",
        "        connection = get_connection()",
        "        cursor = connection.cursor()",
        f"        cursor.execute(DELETE, ({pk_name},))",
        "        connection.commit()",
        "    finally:",
        "        if cursor:",
        "            cursor.close()",
        "        close_connection(connection)",
        "",
    ]
    return "\n".join(lines)


def build_controller(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_name = pk["name"]
    non_pk = _non_pk_fields(definition)

    lines: list[str] = [
        "from core.mvc.controller import BaseController",
        f"from mvc.models.{snake}_model import (",
        f"    get_{plural}, get_{snake}_by_id, add_{snake}, update_{snake}, delete_{snake},",
        ")",
        f"from mvc.forms.{snake}_form import {entity}Form",
        "from mvc.helpers.flash import render_flash_html",
        "",
        "",
        f"def _form_data_from_{snake}(record: dict) -> dict:",
        '    """Convertit les colonnes SQL vers les noms de champs du formulaire."""',
        "    return {",
    ]
    for f in non_pk:
        fname = f["name"]
        fcol = f["column"]
        lines.append(f'        "{fname}": record.get("{fcol}"),')
    lines.append("    }")
    lines.append("")
    lines.append("")
    lines.append(f"class {entity}Controller(BaseController):")

    # index
    lines += [
        "",
        "    @staticmethod",
        "    def index(request):",
        f'        {plural} = get_{plural}()',
        f'        return BaseController.render("{snake}/index.html",',
        f'            context={{"{plural}": {plural}, "flash_html": render_flash_html(request)}},',
        "            request=request)",
    ]

    # new
    lines += [
        "",
        "    @staticmethod",
        "    def new(request):",
        f'        form = {entity}Form()',
        f'        return BaseController.render("{snake}/form.html",',
        f'            context={{"form": form, "action": "/{plural}", "titre": "Nouveau {snake}"}},',
        "            request=request)",
    ]

    # create
    lines += [
        "",
        "    @staticmethod",
        "    def create(request):",
        f'        form = {entity}Form.from_request(request)',
        "        if not form.is_valid():",
        f'            return BaseController.validation_error("{snake}/form.html",',
        f'                context={{"form": form, "action": "/{plural}", "titre": "Nouveau {snake}"}},',
        "                request=request)",
        f'        add_{snake}(form.cleaned_data)',
        f'        return BaseController.redirect_with_flash(request, "/{plural}", "{entity} créé.")',
    ]

    # show
    lines += [
        "",
        "    @staticmethod",
        "    def show(request):",
        f'        {pk_name} = int(request.route_params["id"])',
        f'        {snake} = get_{snake}_by_id({pk_name})',
        f'        if {snake} is None:',
        "            return BaseController.not_found()",
        f'        return BaseController.render("{snake}/show.html",',
        f'            context={{"{snake}": {snake}, "flash_html": render_flash_html(request)}},',
        "            request=request)",
    ]

    # edit
    lines += [
        "",
        "    @staticmethod",
        "    def edit(request):",
        f'        {pk_name} = int(request.route_params["id"])',
        f'        {snake} = get_{snake}_by_id({pk_name})',
        f'        if {snake} is None:',
        "            return BaseController.not_found()",
        f'        return BaseController.render("{snake}/form.html",',
        f'            context={{',
        f'                "form": {entity}Form(_form_data_from_{snake}({snake})),',
        f'                "action": f"/{plural}/{{{pk_name}}}",',
        f'                "titre": "Modifier {snake}",',
        "            },",
        "            request=request)",
    ]

    # update
    lines += [
        "",
        "    @staticmethod",
        "    def update(request):",
        f'        {pk_name} = int(request.route_params["id"])',
        f'        form = {entity}Form.from_request(request)',
        "        if not form.is_valid():",
        f'            return BaseController.validation_error("{snake}/form.html",',
        "                context={",
        '                    "form": form,',
        f'                    "action": f"/{plural}/{{{pk_name}}}",',
        f'                    "titre": "Modifier {snake}",',
        "                },",
        "                request=request)",
        f'        update_{snake}({pk_name}, form.cleaned_data)',
        f'        return BaseController.redirect_with_flash(',
        f'            request, f"/{plural}/{{{pk_name}}}", "{entity} mis à jour.")',
    ]

    # destroy
    lines += [
        "",
        "    @staticmethod",
        "    def destroy(request):",
        f'        {pk_name} = int(request.route_params["id"])',
        f'        delete_{snake}({pk_name})',
        f'        return BaseController.redirect_with_flash(request, "/{plural}", "{entity} supprimé.")',
        "",
    ]

    return "\n".join(lines)


def build_layout() -> str:
    return """\
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ titre | default("Application") }}</title>
    <link rel="icon" href="/static/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="/static/tailwind.css">
</head>
<body class="bg-gray-100 min-h-screen">

    <nav class="bg-blue-700 text-white px-6 py-4 shadow flex justify-between items-center">
        <a href="/" class="text-xl font-bold">Application</a>
        <form method="post" action="/logout" style="display:inline">
            <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
            <button type="submit"
                class="text-sm bg-blue-800 hover:bg-blue-900 px-3 py-1 rounded cursor-pointer">
                Déconnexion
            </button>
        </form>
    </nav>

    <main class="max-w-5xl mx-auto mt-8 px-4">
        {% if flash_html %}
            {{ flash_html | safe }}
        {% endif %}
        {% block content %}{% endblock %}
    </main>

</body>
</html>
"""


def build_index_view(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_col = pk["column"]
    non_pk = _non_pk_fields(definition)

    lines: list[str] = [
        '{% extends "layouts/app.html" %}',
        "{% block content %}",
        '<div class="flex justify-between items-center mb-6">',
        f'    <h1 class="text-2xl font-bold text-gray-800">Liste des {plural}</h1>',
        f'    <a href="/{plural}/new"',
        '       class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">',
        f'        Nouveau {snake}',
        "    </a>",
        "</div>",
        "",
        f"{{% if {plural} %}}",
        '<div class="bg-white shadow rounded overflow-hidden">',
        "    <table class=\"w-full\">",
        "        <thead class=\"bg-gray-50 border-b\">",
        "            <tr>",
    ]
    for f in non_pk:
        label = _humanize(f["name"])
        lines.append(
            f'                <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">'
            f"{label}</th>"
        )
    lines.append(
        '                <th class="px-4 py-3 text-right text-sm font-semibold text-gray-600">Actions</th>'
    )
    lines += [
        "            </tr>",
        "        </thead>",
        "        <tbody class=\"divide-y divide-gray-100\">",
        f"            {{% for {snake} in {plural} %}}",
        "            <tr class=\"hover:bg-gray-50\">",
    ]
    for f in non_pk:
        fcol = f["column"]
        lines.append(
            f'                <td class="px-4 py-3 text-gray-800">'
            f"{{{{ {snake}.{fcol} }}}}</td>"
        )
    lines += [
        '                <td class="px-4 py-3 text-right space-x-2">',
        f'                    <a href="/{plural}/{{{{ {snake}.{pk_col} }}}}"',
        '                       class="text-sm text-blue-600 hover:underline">Voir</a>',
        f'                    <a href="/{plural}/{{{{ {snake}.{pk_col} }}}}/edit"',
        '                       class="text-sm text-blue-600 hover:underline">Modifier</a>',
        f'                    <form method="post" action="/{plural}/{{{{ {snake}.{pk_col} }}}}/delete"',
        '                          style="display:inline">',
        '                        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '                        <button type="submit"',
        '                            class="text-sm text-red-600 hover:underline">Supprimer</button>',
        "                    </form>",
        "                </td>",
        "            </tr>",
        "            {% endfor %}",
        "        </tbody>",
        "    </table>",
        "</div>",
        "{% else %}",
        f'<p class="text-gray-500">Aucun {snake} pour l\'instant.</p>',
        "{% endif %}",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def build_show_view(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_col = pk["column"]
    non_pk = _non_pk_fields(definition)

    lines: list[str] = [
        '{% extends "layouts/app.html" %}',
        "{% block content %}",
        '<div class="flex justify-between items-center mb-6">',
        f'    <h1 class="text-2xl font-bold text-gray-800">Détail {snake}</h1>',
        '    <div class="space-x-2">',
        f'        <a href="/{plural}/{{{{ {snake}.{pk_col} }}}}/edit"',
        '           class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">',
        "            Modifier",
        "        </a>",
        f'        <a href="/{plural}" class="text-gray-600 hover:underline">← Retour</a>',
        "    </div>",
        "</div>",
        "",
        '<div class="bg-white shadow rounded p-6 space-y-4">',
    ]
    for f in non_pk:
        label = _humanize(f["name"])
        fcol = f["column"]
        lines += [
            "    <div>",
            f'        <p class="text-sm text-gray-500">{label}</p>',
            f'        <p class="text-gray-800">{{{{ {snake}.{fcol} }}}}</p>',
            "    </div>",
        ]
    lines += [
        "</div>",
        "",
        f'<form method="post" action="/{plural}/{{{{ {snake}.{pk_col} }}}}/delete" class="mt-4">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        "    <button type=\"submit\"",
        '        class="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700">',
        "        Supprimer",
        "    </button>",
        "</form>",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def build_form_view(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    non_pk = _non_pk_fields(definition)

    lines: list[str] = [
        '{% extends "layouts/app.html" %}',
        "{% block content %}",
        '<div class="flex justify-between items-center mb-6">',
        '    <h1 class="text-2xl font-bold text-gray-800">{{ titre }}</h1>',
        f'    <a href="/{plural}" class="text-gray-600 hover:underline">← Retour</a>',
        "</div>",
        "",
        '{% include "partials/form_errors.html" %}',
        "",
        '<div class="bg-white shadow rounded p-6">',
        '    <form method="post" action="{{ action }}" class="space-y-4">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
    ]

    for f in non_pk:
        fname = f["name"]
        label = _humanize(fname)
        python_type = f.get("python_type", "str")

        _cls = 'class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"'
        if _is_textarea(f):
            lines += [
                "        <div>",
                f'            <label class="block text-sm font-medium text-gray-700">{label}</label>',
                f"            <textarea",
                f'                name="{fname}"',
                f"                {_cls}",
                f"                rows=\"4\">{{{{ form.value('{fname}') }}}}</textarea>",
                f"            {{% if form.has_error('{fname}') %}}",
                f"            <p class=\"text-red-600 text-sm mt-1\">{{{{ form.error('{fname}') }}}}</p>",
                "            {% endif %}",
                "        </div>",
            ]
        elif python_type == "bool":
            lines += [
                '        <div class="flex items-center gap-2">',
                f"            <input",
                f'                type="checkbox"',
                f'                name="{fname}"',
                f'                value="1"',
                f"                {{{{ 'checked' if form.value('{fname}') else '' }}}}",
                "            >",
                f'            <label class="text-sm font-medium text-gray-700">{label}</label>',
                "        </div>",
            ]
        elif python_type in ("int", "float"):
            lines += [
                "        <div>",
                f'            <label class="block text-sm font-medium text-gray-700">{label}</label>',
                f"            <input",
                f'                type="number"',
                f'                name="{fname}"',
                f"                value=\"{{{{ form.value('{fname}') }}}}\"",
                f"                {_cls}",
                "            >",
                f"            {{% if form.has_error('{fname}') %}}",
                f"            <p class=\"text-red-600 text-sm mt-1\">{{{{ form.error('{fname}') }}}}</p>",
                "            {% endif %}",
                "        </div>",
            ]
        else:
            lines += [
                "        <div>",
                f'            <label class="block text-sm font-medium text-gray-700">{label}</label>',
                f"            <input",
                f'                type="text"',
                f'                name="{fname}"',
                f"                value=\"{{{{ form.value('{fname}') }}}}\"",
                f"                {_cls}",
                "            >",
                f"            {{% if form.has_error('{fname}') %}}",
                f"            <p class=\"text-red-600 text-sm mt-1\">{{{{ form.error('{fname}') }}}}</p>",
                "            {% endif %}",
                "        </div>",
            ]

    lines += [
        '        <div class="flex gap-4 pt-2">',
        '            <button type="submit"',
        '                class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">',
        "                Enregistrer",
        "            </button>",
        f'            <a href="/{plural}" class="text-gray-600 hover:underline self-center">Annuler</a>',
        "        </div>",
        "    </form>",
        "</div>",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def _route_block(definition: dict) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    ctrl = f"{entity}Controller"

    return "\n".join([
        "Routes à ajouter dans mvc/routes.py :",
        "─" * 70,
        f"  from mvc.controllers.{snake}_controller import {ctrl}",
        "",
        f"  # Routes protégées par défaut.",
        f"  # Pour un test local sans authentification :",
        f'  # with router.group("/{plural}", public=True, csrf=False) as g:',
        f'  with router.group("/{plural}") as g:',
        f'      g.add("GET",  "",              {ctrl}.index,   name="{snake}_index")',
        f'      g.add("GET",  "/new",          {ctrl}.new,     name="{snake}_new")',
        f'      g.add("POST", "",              {ctrl}.create,  name="{snake}_create")',
        f'      g.add("GET",  "/{{id}}",         {ctrl}.show,    name="{snake}_show")',
        f'      g.add("GET",  "/{{id}}/edit",    {ctrl}.edit,    name="{snake}_edit")',
        f'      g.add("POST", "/{{id}}",         {ctrl}.update,  name="{snake}_update")',
        f'      g.add("POST", "/{{id}}/delete",  {ctrl}.destroy, name="{snake}_destroy")',
    ])


# ── Écriture fichier ───────────────────────────────────────────────────────────

def _write_if_new(path: Path, content: str, result: MakeCrudResult, dry_run: bool) -> None:
    if path.exists():
        result.preserved.append(path)
    else:
        if not dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        result.created.append(path)


# ── Entrée principale ─────────────────────────────────────────────────────────

def make_crud(
    entity_name: str,
    *,
    entities_root: Path,
    output_root: Path,
    dry_run: bool = False,
) -> MakeCrudResult:
    """Génère le scaffolding CRUD pour une entité Forge.

    Raises:
        SystemExit : si l'entité est introuvable ou le JSON invalide.
    """
    snake = _to_snake(entity_name)
    json_path = entities_root / snake / f"{snake}.json"

    if not json_path.exists():
        print(out.error(f"Entité introuvable : {json_path.as_posix()}"))
        raise SystemExit(1)

    try:
        raw = json.loads(json_path.read_text(encoding="utf-8"))
        definition = validate_entity_definition(raw, source=str(json_path))
    except (json.JSONDecodeError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1)

    result = MakeCrudResult(dry_run=dry_run)

    if not _non_pk_fields(definition):
        result.warnings.append(
            f"Entité '{entity_name}' sans champ métier : "
            "formulaire vide, INSERT sans paramètre, UPDATE désactivé."
        )

    form_code, warnings = build_form(definition)
    result.warnings.extend(warnings)

    mvc = output_root / "mvc"

    _write_if_new(
        mvc / "controllers" / f"{snake}_controller.py",
        build_controller(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "models" / f"{snake}_model.py",
        build_model(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "forms" / f"{snake}_form.py",
        form_code,
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / "layouts" / "app.html",
        build_layout(),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "index.html",
        build_index_view(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "show.html",
        build_show_view(definition),
        result, dry_run,
    )
    _write_if_new(
        mvc / "views" / snake / "form.html",
        build_form_view(definition),
        result, dry_run,
    )

    result.route_block = _route_block(definition)
    return result


def cmd_make_crud_main(args: list[str]) -> None:
    if not args or args[0].startswith("-"):
        print("Usage : forge make:crud NomEntite [--dry-run]")
        raise SystemExit(1)

    entity_name = args[0]
    dry_run = "--dry-run" in args
    unknown = [a for a in args[1:] if a != "--dry-run"]
    if unknown:
        print(out.error(f"Arguments inconnus : {' '.join(unknown)}"))
        raise SystemExit(1)

    result = make_crud(
        entity_name,
        entities_root=Path("mvc") / "entities",
        output_root=Path("."),
        dry_run=dry_run,
    )

    for path in result.created:
        print(out.created(path.as_posix()))
    for path in result.preserved:
        print(out.preserved(path.as_posix(), "← fichier existant, non touché"))
    for warn in result.warnings:
        print(out.warn(warn))

    if dry_run:
        print(out.dry_run("Aucun fichier modifié."))

    print()
    print(result.route_block)
    print()
