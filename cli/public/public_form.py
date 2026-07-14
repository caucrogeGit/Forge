# pyright: strict
from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import cli._support.output as out
# Moteur d'entités (forge-mvc-entities) importé paresseusement dans les fonctions
# qui en dépendent (ADR-070) : le cœur n'en dépend pas au chargement.
from cli.public._shared import (
    build_public_routes_file,
    ensure_import as _ensure_import,
    ensure_trailing_newline as _ensure_trailing_newline,
    humanize as _humanize,
    public_routes_branchement,
    require_entities_module as _require_entities_module,
)
from cli.public.public_page import (
    PUBLIC_CONTENT_BLOCK,
    PUBLIC_LAYOUT,
    PUBLIC_SCRIPTS_BLOCK,
    PUBLIC_TITLE_BLOCK,
)
from cli.public.public_list import (
    CONTROLLERS_ROOT,
    ENTITIES_ROOT,
    PUBLIC_TEMPLATE_ROOT,
    SIMPLE_PYTHON_TYPES,
)


_FORM_SENSITIVE_NAMES = {
    "id", "created_at", "updated_at", "password", "password_hash",
    "token", "secret", "is_admin", "is_active", "email_verified_at", "last_login_at",
}
_FORM_SENSITIVE_PARTS = ("password", "token", "secret", "_hash")


@dataclass(frozen=True)
class PublicFormField:
    name: str
    column: str
    label: str
    input_type: str
    required: bool
    python_type: str


@dataclass(frozen=True)
class PublicFormSpec:
    entity: str
    snake: str
    plural: str
    table: str
    pk_column: str
    class_name: str
    route_path: str
    route_new_name: str
    route_create_name: str
    template_name: str
    template_path: Path
    controller_path: Path
    fields: list[PublicFormField]


@dataclass
class MakePublicFormResult:
    spec: PublicFormSpec
    created: list[str] = field(default_factory=list[str])
    preserved: list[str] = field(default_factory=list[str])
    warnings: list[str] = field(default_factory=list[str])


def _is_form_sensitive(field_def: dict[str, Any]) -> bool:
    name = field_def["name"].lower()
    if name in _FORM_SENSITIVE_NAMES:
        return True
    return any(part in name for part in _FORM_SENSITIVE_PARTS)


def _input_type_for(field_def: dict[str, Any]) -> str:
    sql_type = field_def.get("sql_type", "").upper()
    python_type = field_def.get("python_type", "str")
    name = field_def["name"].lower()

    if "TEXT" in sql_type:
        return "textarea"
    if python_type == "bool":
        return "checkbox"
    if python_type in ("int", "float"):
        return "number"
    if python_type == "date":
        return "date"
    if python_type == "datetime":
        return "datetime-local"
    if "email" in name:
        return "email"
    if "url" in name or "website" in name or "site" in name:
        return "url"
    if "phone" in name:
        return "tel"
    return "text"


def public_form_fields(definition: dict[str, Any]) -> list[PublicFormField]:
    fields: list[PublicFormField] = []
    for field_def in definition["fields"]:
        if field_def.get("primary_key"):
            continue
        name = field_def["name"]
        if _is_form_sensitive(field_def):
            continue
        if name.endswith("_id"):
            continue
        python_type = field_def.get("python_type", "str")
        if python_type not in SIMPLE_PYTHON_TYPES:
            continue
        sql_type = field_def.get("sql_type", "").upper()
        if any(kind in sql_type for kind in ("BLOB", "BINARY", "JSON")):
            continue
        fields.append(PublicFormField(
            name=name,
            column=field_def["column"],
            label=_humanize(name),
            input_type=_input_type_for(field_def),
            required=not field_def.get("nullable", False),
            python_type=python_type,
        ))
    return fields


def build_public_form_spec(definition: dict[str, Any]) -> PublicFormSpec:
    from forge_mvc_entities import pk_field, to_snake
    entity = definition["entity"]
    snake = to_snake(entity)
    plural = snake + "s"
    pk = pk_field(definition)
    class_name = "Public" + "".join(part.capitalize() for part in plural.split("_")) + "Controller"
    template_path = PUBLIC_TEMPLATE_ROOT / plural / "form.html"
    controller_path = CONTROLLERS_ROOT / f"public_{plural}_controller.py"
    return PublicFormSpec(
        entity=entity,
        snake=snake,
        plural=plural,
        table=definition["table"],
        pk_column=pk["column"],
        class_name=class_name,
        route_path=f"/{plural}",
        route_new_name=f"public_{plural}-new",
        route_create_name=f"public_{plural}-create",
        template_name=f"public/{plural}/form.html",
        template_path=template_path,
        controller_path=controller_path,
        fields=public_form_fields(definition),
    )


def _build_insert_sql(spec: PublicFormSpec) -> str:
    if not spec.fields:
        return f"INSERT INTO {spec.table} () VALUES ()"
    columns = ", ".join(f.column for f in spec.fields)
    placeholders = ", ".join("?" for _ in spec.fields)
    return f"INSERT INTO {spec.table} ({columns}) VALUES ({placeholders})"


def _build_form_fields_repr(spec: PublicFormSpec) -> str:
    if not spec.fields:
        return "[]"
    items = [
        f'{{"name": "{f.name}", "label": "{f.label}", "input_type": "{f.input_type}", "required": {f.required}}}'
        for f in spec.fields
    ]
    return "[\n" + "".join(f"    {item},\n" for item in items) + "]"


def build_public_form_new_method(spec: PublicFormSpec) -> str:
    return "".join([
        "\n",
        "    @staticmethod\n",
        "    def new(request: Request) -> Response:\n",
        "        return BaseController.render(\n",
        f'            "{spec.template_name}",\n',
        "            context={\n",
        '                "fields": FORM_FIELDS,\n',
        '                "errors": {},\n',
        '                "form_data": {},\n',
        '                "flash": get_flash(get_session_id(request)),\n',
        "            },\n",
        "            request=request,\n",
        "        )\n",
    ])


def build_public_form_create_method(spec: PublicFormSpec) -> str:
    return "".join([
        "\n",
        "    @staticmethod\n",
        "    def create(request: Request) -> Response:\n",
        "        errors = {}\n",
        "        form_data = {}\n",
        "        for _field in FORM_FIELDS:\n",
        '            _raw = request.form(_field["name"], "")\n',
        '            form_data[_field["name"]] = _raw\n',
        '            if _field["required"] and not str(_raw).strip():\n',
        '                errors[_field["name"]] = f\'{_field["label"]} est requis.\'\n',
        "        if errors:\n",
        "            return BaseController.render(\n",
        f'                "{spec.template_name}",\n',
        "                context={\n",
        '                    "fields": FORM_FIELDS,\n',
        '                    "errors": errors,\n',
        '                    "form_data": form_data,\n',
        '                    "flash": None,\n',
        "                },\n",
        "                request=request,\n",
        "            )\n",
        "        _values = []\n",
        "        for _field in FORM_FIELDS:\n",
        '            _raw = form_data[_field["name"]]\n',
        '            if _field["input_type"] == "checkbox":\n',
        "                _values.append(1 if _raw else 0)\n",
        "            else:\n",
        "                _values.append(_raw if str(_raw).strip() else None)\n",
        "        connection = None\n",
        "        cursor = None\n",
        "        try:\n",
        "            connection = get_connection()\n",
        "            cursor = connection.cursor()\n",
        "            cursor.execute(INSERT_PUBLIC_FORM, _values)\n",
        "            connection.commit()\n",
        "        finally:\n",
        "            if cursor:\n",
        "                cursor.close()\n",
        "            close_connection(connection)\n",
        "        return BaseController.redirect_with_flash(\n",
        "            request,\n",
        f'            "{spec.route_path}/new",\n',
        '            "Votre demande a été envoyée.",\n',
        "        )\n",
    ])


def build_public_form_controller(spec: PublicFormSpec) -> str:
    return "".join([
        "from core.database.connection import get_connection, close_connection\n",
        "from core.http.request import Request\n",
        "from core.http.response import Response\n",
        "from core.mvc.controller.base_controller import BaseController\n",
        "from core.security.session import get_flash, get_session_id\n",
        "\n",
        "\n",
        f'INSERT_PUBLIC_FORM = "{_build_insert_sql(spec)}"\n',
        f"FORM_FIELDS = {_build_form_fields_repr(spec)}\n",
        "\n",
        "\n",
        f"class {spec.class_name}(BaseController):\n",
        build_public_form_new_method(spec),
        build_public_form_create_method(spec),
    ])


def build_public_form_template(spec: PublicFormSpec) -> str:
    title = _humanize(spec.entity)
    lines = [
        f'{{% extends "{PUBLIC_LAYOUT}" %}}',
        "",
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}{title}{{% endblock %}}",
        "",
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}",
        '<section class="mx-auto max-w-2xl px-6 py-12">',
        '    {% from "components/ui.html" import flash_messages %}{{ flash_messages(flash) }}',
        f'    <h1 class="text-3xl font-bold text-gray-900">{title}</h1>',
        f'    <form method="post" action="{spec.route_path}" class="mt-8 space-y-6">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        "        {% for field in fields %}",
        "        <div>",
        '            <label for="{{ field.name }}" class="block text-sm font-medium text-gray-700">',
        '                {{ field.label }}{% if field.required %} <span class="text-red-500">*</span>{% endif %}',
        "            </label>",
        '            {% if field.input_type == "textarea" %}',
        '            <textarea id="{{ field.name }}" name="{{ field.name }}"',
        '                      class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm"',
        '                      {% if field.required %}required{% endif %}>{{ form_data[field.name] or "" }}</textarea>',
        '            {% elif field.input_type == "checkbox" %}',
        '            <input type="checkbox" id="{{ field.name }}" name="{{ field.name }}"',
        '                   class="mt-1 h-4 w-4 rounded border-gray-300"',
        "                   {% if form_data[field.name] %}checked{% endif %}>",
        "            {% else %}",
        '            <input type="{{ field.input_type }}" id="{{ field.name }}" name="{{ field.name }}"',
        "                   value=\"{{ form_data[field.name] or '' }}\"",
        '                   class="mt-1 block w-full rounded border border-gray-300 px-3 py-2 shadow-sm"',
        "                   {% if field.required %}required{% endif %}>",
        "            {% endif %}",
        "            {% if field.name in errors %}",
        '            <p class="mt-1 text-sm text-red-600">{{ errors[field.name] }}</p>',
        "            {% endif %}",
        "        </div>",
        "        {% endfor %}",
        '        <button type="submit" class="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">',
        "            Envoyer",
        "        </button>",
        "    </form>",
        "</section>",
        "{% endblock %}",
        "",
        f"{{% block {PUBLIC_SCRIPTS_BLOCK} %}}{{% endblock %}}",
        "",
    ]
    return "\n".join(lines)


def _write_form_routes(project_root: Path, result: "MakePublicFormResult", spec: PublicFormSpec) -> None:
    """Écrit mvc/routes/public_<plural>_form_routes.py en write-if-new (ADR-085)."""
    register_name = f"public_{spec.plural}_form"
    routes_rel = Path("mvc/routes") / f"{register_name}_routes.py"
    routes_path = project_root / routes_rel
    routes_path.parent.mkdir(parents=True, exist_ok=True)
    if routes_path.exists():
        result.preserved.append(routes_rel.as_posix())
        return
    routes_path.write_text(
        build_public_routes_file(
            register_name,
            f"from mvc.controllers.public_{spec.plural}_controller import {spec.class_name}",
            [
                f'public.add("GET", "{spec.route_path}/new", {spec.class_name}.new, '
                f'name="{spec.route_new_name}")',
                f'public.add("POST", "{spec.route_path}", {spec.class_name}.create, '
                f'name="{spec.route_create_name}")',
            ],
        ),
        encoding="utf-8",
    )
    result.created.append(routes_rel.as_posix())


def _ensure_insert_constant(content: str, spec: PublicFormSpec) -> tuple[str, bool]:
    if "INSERT_PUBLIC_FORM" in content:
        return content, False
    constant = f'INSERT_PUBLIC_FORM = "{_build_insert_sql(spec)}"\n'
    marker = f"class {spec.class_name}(BaseController):"
    if marker in content:
        return content.replace(marker, constant + "\n" + marker, 1), True
    return content, False


def _ensure_form_fields_constant(content: str, spec: PublicFormSpec) -> tuple[str, bool]:
    if "FORM_FIELDS" in content:
        return content, False
    constant = f"FORM_FIELDS = {_build_form_fields_repr(spec)}\n"
    if "INSERT_PUBLIC_FORM" in content:
        lines = _ensure_trailing_newline(content).splitlines(keepends=True)
        for index, line in enumerate(lines):
            if line.startswith("INSERT_PUBLIC_FORM"):
                lines.insert(index + 1, constant)
                return "".join(lines), True
    marker = f"class {spec.class_name}(BaseController):"
    if marker in content:
        return content.replace(marker, constant + "\n" + marker, 1), True
    return content, False


def _ensure_form_controller(controller_path: Path, spec: PublicFormSpec) -> tuple[bool, str | None]:
    if not controller_path.exists():
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.write_text(build_public_form_controller(spec), encoding="utf-8")
        return True, None

    content = controller_path.read_text(encoding="utf-8")
    if re.search(r"^\s+def\s+new\s*\(", content, re.MULTILINE) or re.search(
        r"^\s+def\s+create\s*\(", content, re.MULTILINE
    ):
        return False, None

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False, f"Contrôleur non modifié automatiquement : {controller_path.as_posix()}"

    target_class = next(
        (node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == spec.class_name),
        None,
    )
    if target_class is None or target_class.end_lineno is None:
        return False, f"Contrôleur à compléter manuellement : {controller_path.as_posix()}"

    content, _ = _ensure_import(
        content, "from core.database.connection import get_connection, close_connection"
    )
    content, _ = _ensure_import(
        content, "from core.mvc.controller.base_controller import BaseController"
    )
    content, _ = _ensure_import(
        content, "from core.security.session import get_flash, get_session_id"
    )
    content, _ = _ensure_insert_constant(content, spec)
    content, _ = _ensure_form_fields_constant(content, spec)

    tree = ast.parse(content)
    target_class = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == spec.class_name
    )
    lines = _ensure_trailing_newline(content).splitlines(keepends=True)
    lines.insert(
        target_class.end_lineno or len(lines),
        build_public_form_new_method(spec) + build_public_form_create_method(spec),
    )
    controller_path.write_text("".join(lines), encoding="utf-8")
    return True, None


def load_public_form_definition(entity_name: str, *, entities_root: Path) -> dict[str, Any]:
    from forge_mvc_entities import to_snake
    from forge_mvc_entities.validation import validate_entity_definition
    snake = to_snake(entity_name)
    json_path = entities_root / snake / f"{snake}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Entité introuvable : {json_path.as_posix()}")
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    return validate_entity_definition(raw, source=str(json_path))


def make_public_form(
    entity_name: str,
    *,
    entities_root: Path | None = None,
    output_root: Path | None = None,
) -> MakePublicFormResult:
    project_root = (output_root or Path.cwd()).resolve()
    definition = load_public_form_definition(
        entity_name,
        entities_root=entities_root or project_root / ENTITIES_ROOT,
    )
    spec = build_public_form_spec(definition)
    result = MakePublicFormResult(spec=spec)

    template_path = project_root / spec.template_path
    template_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        result.preserved.append(spec.template_path.as_posix())
    else:
        template_path.write_text(build_public_form_template(spec), encoding="utf-8")
        result.created.append(spec.template_path.as_posix())

    controller_changed, controller_warning = _ensure_form_controller(
        project_root / spec.controller_path,
        spec,
    )
    if controller_changed:
        result.created.append(spec.controller_path.as_posix())
    else:
        result.preserved.append(spec.controller_path.as_posix())
    if controller_warning:
        result.warnings.append(controller_warning)

    # ADR-085 : fichier de routes dédié + affichage, jamais d'injection.
    _write_form_routes(project_root, result, spec)

    if not spec.fields:
        result.warnings.append(f"Aucun champ public affichable détecté pour {spec.entity}.")

    return result


def print_result(result: MakePublicFormResult) -> None:
    spec = result.spec
    print(f"Formulaire public généré : {spec.entity}")
    print(f"Routes : GET {spec.route_path}/new  POST {spec.route_path}")
    print(f"Template : {spec.template_path.as_posix()}")
    print(f"Contrôleur : {spec.controller_path.as_posix()}")
    for path in result.created:
        print(out.created(path))
    for path in result.preserved:
        print(out.preserved(path))
    for warning in result.warnings:
        print(out.warn(warning))
    print()
    print(public_routes_branchement(f"public_{spec.plural}_form"))


def main(args: list[str], *, root: Path | None = None) -> MakePublicFormResult:
    if len(args) != 1:
        raise SystemExit("Usage : forge make:public-form <Entite>")
    _require_entities_module()
    project_root = root or Path.cwd()
    try:
        result = make_public_form(
            args[0],
            entities_root=project_root / ENTITIES_ROOT,
            output_root=project_root,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1) from exc
    print_result(result)
    return result
