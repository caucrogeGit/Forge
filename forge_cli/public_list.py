from __future__ import annotations

import json
import re
import ast
from dataclasses import dataclass, field
from pathlib import Path

import forge_cli.output as out
from forge_cli.entities.make_crud import _pk_field, _to_snake
from forge_cli.entities.validation import validate_entity_definition
from forge_cli.public_page import (
    PUBLIC_CONTENT_BLOCK,
    PUBLIC_LAYOUT,
    PUBLIC_SCRIPTS_BLOCK,
    PUBLIC_TITLE_BLOCK,
    ROUTES_PATH,
    _ensure_routes_file,
    _ensure_trailing_newline,
    _insert_import,
)


PUBLIC_TEMPLATE_ROOT = Path("mvc/views/public")
CONTROLLERS_ROOT = Path("mvc/controllers")
ENTITIES_ROOT = Path("mvc/entities")
SENSITIVE_FIELD_NAMES = {
    "id",
    "created_at",
    "updated_at",
    "password",
    "password_hash",
    "token",
    "secret",
}
SENSITIVE_FIELD_PARTS = ("password", "token", "secret")
SIMPLE_PYTHON_TYPES = {"str", "int", "float", "bool", "date", "datetime"}


@dataclass(frozen=True)
class PublicListField:
    name: str
    column: str
    label: str


@dataclass(frozen=True)
class PublicMediaEntry:
    name: str
    label: str
    role: str
    field_type: str
    multiple: bool


@dataclass(frozen=True)
class PublicListSpec:
    entity: str
    snake: str
    plural: str
    table: str
    pk_column: str
    class_name: str
    route_path: str
    route_name: str
    template_name: str
    template_path: Path
    show_route_path: str
    show_route_name: str
    show_template_name: str
    show_template_path: Path
    controller_path: Path
    fields: list[PublicListField]
    media_entries: list[PublicMediaEntry]


@dataclass
class MakePublicListResult:
    spec: PublicListSpec
    created: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class MakePublicShowResult:
    spec: PublicListSpec
    created: list[str] = field(default_factory=list)
    preserved: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _humanize(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _is_sensitive_field(field: dict) -> bool:
    name = field["name"].lower()
    if name in SENSITIVE_FIELD_NAMES:
        return True
    return any(part in name for part in SENSITIVE_FIELD_PARTS)


def public_list_fields(definition: dict) -> list[PublicListField]:
    fields: list[PublicListField] = []
    for field_def in definition["fields"]:
        if field_def.get("primary_key"):
            continue
        name = field_def["name"]
        if _is_sensitive_field(field_def):
            continue
        if name.endswith("_id"):
            continue
        if field_def.get("python_type") not in SIMPLE_PYTHON_TYPES:
            continue
        sql_type = field_def.get("sql_type", "").upper()
        if any(kind in sql_type for kind in ("BLOB", "BINARY", "JSON")):
            continue
        fields.append(
            PublicListField(
                name=name,
                column=field_def["column"],
                label=_humanize(name),
            )
        )
    return fields


def public_media_entries(definition: dict) -> list[PublicMediaEntry]:
    entries = []
    for m in definition.get("media") or []:
        if not isinstance(m, dict):
            continue
        field_type = m.get("field", "")
        if field_type not in ("image", "file"):
            continue
        entries.append(PublicMediaEntry(
            name=m["name"],
            label=m.get("label") or _humanize(m["name"]),
            role=m["role"],
            field_type=field_type,
            multiple=bool(m.get("multiple", False)),
        ))
    return entries


def _list_cover_entry(spec: PublicListSpec) -> PublicMediaEntry | None:
    for e in spec.media_entries:
        if e.field_type == "image":
            return e
    return None


def _media_import_line(spec: PublicListSpec) -> str | None:
    if not spec.media_entries:
        return None
    funcs: set[str] = set()
    for e in spec.media_entries:
        if e.multiple:
            funcs.add("list_media_for_entity")
        else:
            funcs.add("get_cover_media")
    if not funcs:
        return None
    return f"from forge_mvc_images import {', '.join(sorted(funcs))}"


def _list_select_columns(spec: PublicListSpec) -> str:
    cover = _list_cover_entry(spec)
    parts = []
    if cover is not None:
        parts.append(f"{spec.pk_column} AS _entity_id")
    parts += [f"{f.column} AS {f.name}" for f in spec.fields]
    return ", ".join(parts) if parts else f"{spec.pk_column} AS _public_id"


def load_public_list_definition(entity_name: str, *, entities_root: Path) -> dict:
    snake = _to_snake(entity_name)
    json_path = entities_root / snake / f"{snake}.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Entité introuvable : {json_path.as_posix()}")
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    return validate_entity_definition(raw, source=str(json_path))


def build_public_list_spec(definition: dict) -> PublicListSpec:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    class_name = "Public" + "".join(part.capitalize() for part in plural.split("_")) + "Controller"
    template_path = PUBLIC_TEMPLATE_ROOT / plural / "index.html"
    controller_path = CONTROLLERS_ROOT / f"public_{plural}_controller.py"
    return PublicListSpec(
        entity=entity,
        snake=snake,
        plural=plural,
        table=definition["table"],
        pk_column=pk["column"],
        class_name=class_name,
        route_path=f"/{plural}",
        route_name=f"public_{plural}_index",
        template_name=f"public/{plural}/index.html",
        template_path=template_path,
        show_route_path=f"/{plural}/{{id}}",
        show_route_name=f"public_{plural}_show",
        show_template_name=f"public/{plural}/show.html",
        show_template_path=PUBLIC_TEMPLATE_ROOT / plural / "show.html",
        controller_path=controller_path,
        fields=public_list_fields(definition),
        media_entries=public_media_entries(definition),
    )


def _select_columns(spec: PublicListSpec) -> str:
    if not spec.fields:
        return f"{spec.pk_column} AS _public_id"
    return ", ".join(f"{field.column} AS {field.name}" for field in spec.fields)


def build_public_list_controller(spec: PublicListSpec) -> str:
    context_fields = repr(
        [{"name": field.name, "label": field.label} for field in spec.fields]
    )
    cover = _list_cover_entry(spec)
    parts: list[str] = [
        "from core.database.connection import get_connection, close_connection\n",
        "from core.http.request import Request\n",
        "from core.http.response import Response\n",
        "from core.mvc.controller.base_controller import BaseController\n",
    ]
    if cover is not None:
        parts.append("from forge_mvc_images import get_cover_media\n")
    parts += [
        "\n",
        "\n",
        f'SELECT_PUBLIC_LIST = "SELECT {_list_select_columns(spec)} FROM {spec.table} '
        f'ORDER BY {spec.pk_column} DESC"\n',
        "\n",
        "\n",
        f"class {spec.class_name}(BaseController):\n",
        "\n",
        "    @staticmethod\n",
        "    def index(request: Request) -> Response:\n",
        "        connection = None\n",
        "        cursor = None\n",
        "        try:\n",
        "            connection = get_connection()\n",
        "            cursor = connection.cursor(dictionary=True)\n",
        "            cursor.execute(SELECT_PUBLIC_LIST)\n",
        "            rows = cursor.fetchall()\n",
        "        finally:\n",
        "            if cursor:\n",
        "                cursor.close()\n",
        "            close_connection(connection)\n",
    ]
    if cover is not None:
        parts += [
            "        for _row in rows:\n",
            f'            _row["_cover_media"] = get_cover_media("{spec.snake}", _row["_entity_id"], role="{cover.role}")\n',
        ]
    parts += [
        "        return BaseController.render(\n",
        f'            "{spec.template_name}",\n',
        "            context={\n",
        f'                "{spec.plural}": rows,\n',
        f'                "fields": {context_fields},\n',
        "            },\n",
        "            request=request,\n",
        "        )\n",
    ]
    return "".join(parts)


def build_public_show_controller(spec: PublicListSpec) -> str:
    context_fields = repr(
        [{"name": field.name, "label": field.label} for field in spec.fields]
    )
    media_import = _media_import_line(spec)
    parts: list[str] = [
        "from core.database.connection import get_connection, close_connection\n",
        "from core.http.request import Request\n",
        "from core.http.response import Response\n",
        "from core.mvc.controller.base_controller import BaseController\n",
    ]
    if media_import:
        parts.append(f"{media_import}\n")
    parts += [
        "\n",
        "\n",
        f'SELECT_PUBLIC_DETAIL = "SELECT {_select_columns(spec)} FROM {spec.table} '
        f'WHERE {spec.pk_column} = ?"\n',
        "\n",
        "\n",
        f"class {spec.class_name}(BaseController):\n",
        build_public_show_method(spec, context_fields=context_fields),
    ]
    return "".join(parts)


def build_public_show_method(
    spec: PublicListSpec,
    *,
    context_fields: str | None = None,
) -> str:
    context_fields = context_fields or repr(
        [{"name": field.name, "label": field.label} for field in spec.fields]
    )
    parts: list[str] = [
        "\n",
        "    @staticmethod\n",
        "    def show(request: Request) -> Response:\n",
        "        public_id = request.route_params.get(\"id\")\n",
        "        connection = None\n",
        "        cursor = None\n",
        "        try:\n",
        "            connection = get_connection()\n",
        "            cursor = connection.cursor(dictionary=True)\n",
        "            cursor.execute(SELECT_PUBLIC_DETAIL, (public_id,))\n",
        "            row = cursor.fetchone()\n",
        "        finally:\n",
        "            if cursor:\n",
        "                cursor.close()\n",
        "            close_connection(connection)\n",
        "        if not row:\n",
        "            return BaseController.not_found()\n",
    ]
    context_extras: list[str] = []
    for entry in spec.media_entries:
        if entry.multiple:
            var = f"{entry.name}_media_list"
            parts.append(
                f'        {var} = list_media_for_entity("{spec.snake}", int(public_id), role="{entry.role}")\n'
            )
        else:
            var = f"{entry.name}_media"
            parts.append(
                f'        {var} = get_cover_media("{spec.snake}", int(public_id), role="{entry.role}")\n'
            )
        context_extras.append(f'                "{var}": {var},\n')
    parts += [
        "        return BaseController.render(\n",
        f'            "{spec.show_template_name}",\n',
        "            context={\n",
        f'                "{spec.snake}": row,\n',
        f'                "fields": {context_fields},\n',
        f'                "back_url": "{spec.route_path}",\n',
    ]
    parts.extend(context_extras)
    parts += [
        "            },\n",
        "            request=request,\n",
        "        )\n",
    ]
    return "".join(parts)


def build_public_list_template(spec: PublicListSpec) -> str:
    rows_key = spec.plural
    title = _humanize(spec.plural)
    cover = _list_cover_entry(spec)
    lines = [
        f'{{% extends "{PUBLIC_LAYOUT}" %}}',
        "",
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}{title}{{% endblock %}}",
        "",
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}",
        '<section class="mx-auto max-w-5xl px-6 py-12">',
        f'    <h1 class="text-3xl font-bold text-gray-900">{title}</h1>',
        "",
        f"    {{% if {rows_key} %}}",
        '    <div class="mt-8 overflow-hidden rounded border border-gray-200 bg-white">',
        '        <table class="min-w-full divide-y divide-gray-200">',
        '            <thead class="bg-gray-50">',
        "                <tr>",
    ]
    if cover is not None:
        lines.append(
            f'                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700">{cover.label}</th>'
        )
    lines += [
        "                    {% for field in fields %}",
        '                    <th class="px-4 py-3 text-left text-sm font-semibold text-gray-700">{{ field.label }}</th>',
        "                    {% endfor %}",
        "                </tr>",
        "            </thead>",
        '            <tbody class="divide-y divide-gray-100">',
        f"                {{% for row in {rows_key} %}}",
        "                <tr>",
    ]
    if cover is not None:
        lines += [
            '                    <td class="px-4 py-3">',
            "                        {% if row._cover_media %}",
            '                        <img src="{{ row._cover_media.thumbnail_url or row._cover_media.url }}"',
            f'                             alt="{{{{ row._cover_media.alt_text or \'{cover.label}\' }}}}"',
            '                             class="h-12 w-12 rounded object-cover">',
            "                        {% endif %}",
            "                    </td>",
        ]
    lines += [
        "                    {% for field in fields %}",
        '                    <td class="px-4 py-3 text-sm text-gray-800">{{ row[field.name] }}</td>',
        "                    {% endfor %}",
        "                </tr>",
        "                {% endfor %}",
        "            </tbody>",
        "        </table>",
        "    </div>",
        "    {% else %}",
        '    <div class="mt-8 rounded border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">',
        "        {{ trans('public.list.empty') }}",
        "    </div>",
        "    {% endif %}",
        "</section>",
        "{% endblock %}",
        "",
        f"{{% block {PUBLIC_SCRIPTS_BLOCK} %}}{{% endblock %}}",
        "",
    ]
    return "\n".join(lines)


def build_public_show_template(spec: PublicListSpec) -> str:
    title = _humanize(spec.entity)
    lines = [
        f'{{% extends "{PUBLIC_LAYOUT}" %}}',
        "",
        f"{{% block {PUBLIC_TITLE_BLOCK} %}}{title}{{% endblock %}}",
        "",
        f"{{% block {PUBLIC_CONTENT_BLOCK} %}}",
        '<section class="mx-auto max-w-5xl px-6 py-12">',
        '    <a href="{{ back_url }}" class="text-sm text-gray-600 hover:underline">{{ trans(\'public.show.back\') }}</a>',
        f'    <h1 class="mt-4 text-3xl font-bold text-gray-900">{title}</h1>',
        "",
        f"    {{% if {spec.snake} %}}",
        '    <dl class="mt-8 divide-y divide-gray-200 rounded border border-gray-200 bg-white">',
        "        {% for field in fields %}",
        '        <div class="grid gap-2 px-4 py-4 sm:grid-cols-3">',
        '            <dt class="text-sm font-medium text-gray-600">{{ field.label }}</dt>',
        f'            <dd class="text-sm text-gray-900 sm:col-span-2">{{{{ {spec.snake}[field.name] }}}}</dd>',
        "        </div>",
        "        {% endfor %}",
        "    </dl>",
    ]
    for entry in spec.media_entries:
        if entry.multiple:
            ctx_var = f"{entry.name}_media_list"
            if entry.field_type == "image":
                lines += [
                    f"    {{% if {ctx_var} %}}",
                    '    <div class="mt-8">',
                    f'        <p class="text-sm font-medium text-gray-600">{entry.label}</p>',
                    '        <div class="mt-2 flex flex-wrap gap-2">',
                    f"            {{% for _m in {ctx_var} %}}",
                    '            <img src="{{ _m.thumbnail_url or _m.url }}"',
                    f'                 alt="{{{{ _m.alt_text or \'{entry.label}\' }}}}"',
                    '                 class="h-24 rounded object-cover">',
                    "            {% endfor %}",
                    "        </div>",
                    "    </div>",
                    "    {% endif %}",
                ]
            else:
                lines += [
                    f"    {{% if {ctx_var} %}}",
                    '    <div class="mt-8">',
                    f'        <p class="text-sm font-medium text-gray-600">{entry.label}</p>',
                    '        <ul class="mt-2 space-y-1">',
                    f"            {{% for _m in {ctx_var} %}}",
                    '            <li><a href="{{ _m.url }}" class="text-sm text-blue-600 hover:underline">{{ _m.original_name or "Fichier" }}</a></li>',
                    "            {% endfor %}",
                    "        </ul>",
                    "    </div>",
                    "    {% endif %}",
                ]
        else:
            ctx_var = f"{entry.name}_media"
            if entry.field_type == "image":
                lines += [
                    f"    {{% if {ctx_var} %}}",
                    '    <div class="mt-8">',
                    f'        <p class="text-sm font-medium text-gray-600">{entry.label}</p>',
                    f'        <img src="{{{{ {ctx_var}.thumbnail_url or {ctx_var}.url }}}}"',
                    f'             alt="{{{{ {ctx_var}.alt_text or \'{entry.label}\' }}}}"',
                    '             class="mt-2 h-48 rounded object-cover">',
                    "    </div>",
                    "    {% endif %}",
                ]
            else:
                lines += [
                    f"    {{% if {ctx_var} %}}",
                    '    <div class="mt-8">',
                    f'        <p class="text-sm font-medium text-gray-600">{entry.label}</p>',
                    f'        <a href="{{{{ {ctx_var}.url }}}}" class="mt-2 text-sm text-blue-600 hover:underline">{{{{ {ctx_var}.original_name or "Voir le fichier" }}}}</a>',
                    "    </div>",
                    "    {% endif %}",
                ]
    lines += [
        "    {% else %}",
        '    <div class="mt-8 rounded border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">',
        "        {{ trans('public.show.not_found') }}",
        "    </div>",
        "    {% endif %}",
        "</section>",
        "{% endblock %}",
        "",
        f"{{% block {PUBLIC_SCRIPTS_BLOCK} %}}{{% endblock %}}",
        "",
    ]
    return "\n".join(lines)


def _route_exists(content: str, spec: PublicListSpec) -> bool:
    path_pattern = rf'["\']{re.escape(spec.route_path)}["\']'
    route_name = f'name="{spec.route_name}"'
    return re.search(path_pattern, content) is not None or route_name in content


def build_route_block(spec: PublicListSpec) -> str:
    return (
        "\n"
        "with router.group(\"\", public=True) as pub:\n"
        f'    pub.add("GET", "{spec.route_path}", {spec.class_name}.index, '
        f'name="{spec.route_name}")\n'
    )


def build_show_route_block(spec: PublicListSpec) -> str:
    return (
        "\n"
        "with router.group(\"\", public=True) as pub:\n"
        f'    pub.add("GET", "{spec.show_route_path}", {spec.class_name}.show, '
        f'name="{spec.show_route_name}")\n'
    )


def _ensure_route(routes_path: Path, spec: PublicListSpec) -> tuple[bool, str | None]:
    _ensure_routes_file(routes_path)
    content = routes_path.read_text(encoding="utf-8")
    import_line = (
        f"from mvc.controllers.public_{spec.plural}_controller import {spec.class_name}"
    )
    changed = import_line not in content
    content = _insert_import(content, import_line)

    if _route_exists(content, spec):
        routes_path.write_text(_ensure_trailing_newline(content), encoding="utf-8")
        return changed, None

    if "router = Router()" not in content:
        return False, f"Route à ajouter manuellement dans {routes_path.as_posix()} : GET {spec.route_path}"

    routes_path.write_text(
        _ensure_trailing_newline(content) + build_route_block(spec),
        encoding="utf-8",
    )
    return True, None


def _show_route_exists(content: str, spec: PublicListSpec) -> bool:
    route_name = f'name="{spec.show_route_name}"'
    route_path = re.escape(spec.show_route_path)
    path_pattern = rf'["\']{route_path}["\']'
    return re.search(path_pattern, content) is not None or route_name in content


def _ensure_show_route(routes_path: Path, spec: PublicListSpec) -> tuple[bool, str | None]:
    _ensure_routes_file(routes_path)
    content = routes_path.read_text(encoding="utf-8")
    import_line = (
        f"from mvc.controllers.public_{spec.plural}_controller import {spec.class_name}"
    )
    changed = import_line not in content
    content = _insert_import(content, import_line)

    if _show_route_exists(content, spec):
        routes_path.write_text(_ensure_trailing_newline(content), encoding="utf-8")
        return changed, None

    if "router = Router()" not in content:
        return False, f"Route à ajouter manuellement dans {routes_path.as_posix()} : GET {spec.show_route_path}"

    routes_path.write_text(
        _ensure_trailing_newline(content) + build_show_route_block(spec),
        encoding="utf-8",
    )
    return True, None


def _ensure_import(content: str, import_line: str) -> tuple[str, bool]:
    if import_line in content:
        return content, False
    return _insert_import(content, import_line), True


def _ensure_detail_constant(content: str, spec: PublicListSpec) -> tuple[str, bool]:
    if "SELECT_PUBLIC_DETAIL" in content:
        return content, False
    constant = (
        f'SELECT_PUBLIC_DETAIL = "SELECT {_select_columns(spec)} FROM {spec.table} '
        f'WHERE {spec.pk_column} = ?"\n'
    )
    if "SELECT_PUBLIC_LIST" in content:
        lines = _ensure_trailing_newline(content).splitlines(keepends=True)
        for index, line in enumerate(lines):
            if line.startswith("SELECT_PUBLIC_LIST"):
                lines.insert(index + 1, constant)
                return "".join(lines), True
    marker = f"class {spec.class_name}(BaseController):"
    if marker in content:
        return content.replace(marker, constant + "\n" + marker, 1), True
    return content, False


def _ensure_show_controller(controller_path: Path, spec: PublicListSpec) -> tuple[bool, str | None]:
    if not controller_path.exists():
        controller_path.parent.mkdir(parents=True, exist_ok=True)
        controller_path.write_text(build_public_show_controller(spec), encoding="utf-8")
        return True, None

    content = controller_path.read_text(encoding="utf-8")
    if re.search(r"^\s+def\s+show\s*\(", content, re.MULTILINE):
        return False, None

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return False, f"Contrôleur non modifié automatiquement : {controller_path.as_posix()}"

    target_class = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == spec.class_name
        ),
        None,
    )
    if target_class is None or target_class.end_lineno is None:
        return False, f"Contrôleur à compléter manuellement : {controller_path.as_posix()}"

    content, _ = _ensure_import(
        content,
        "from core.database.connection import get_connection, close_connection",
    )
    content, _ = _ensure_import(
        content,
        "from core.mvc.controller.base_controller import BaseController",
    )
    media_import = _media_import_line(spec)
    if media_import:
        content, _ = _ensure_import(content, media_import)
    content, _ = _ensure_detail_constant(content, spec)

    tree = ast.parse(content)
    target_class = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == spec.class_name
    )
    lines = _ensure_trailing_newline(content).splitlines(keepends=True)
    lines.insert(target_class.end_lineno or len(lines), build_public_show_method(spec))
    controller_path.write_text("".join(lines), encoding="utf-8")
    return True, None


def make_public_list(
    entity_name: str,
    *,
    entities_root: Path | None = None,
    output_root: Path | None = None,
) -> MakePublicListResult:
    project_root = (output_root or Path.cwd()).resolve()
    definition = load_public_list_definition(
        entity_name,
        entities_root=entities_root or project_root / ENTITIES_ROOT,
    )
    spec = build_public_list_spec(definition)
    result = MakePublicListResult(spec=spec)

    template_path = project_root / spec.template_path
    template_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        result.preserved.append(spec.template_path.as_posix())
    else:
        template_path.write_text(build_public_list_template(spec), encoding="utf-8")
        result.created.append(spec.template_path.as_posix())

    controller_path = project_root / spec.controller_path
    controller_path.parent.mkdir(parents=True, exist_ok=True)
    if controller_path.exists():
        result.preserved.append(spec.controller_path.as_posix())
    else:
        controller_path.write_text(build_public_list_controller(spec), encoding="utf-8")
        result.created.append(spec.controller_path.as_posix())

    route_changed, route_warning = _ensure_route(project_root / ROUTES_PATH, spec)
    if route_changed:
        result.created.append(ROUTES_PATH.as_posix())
    else:
        result.preserved.append(ROUTES_PATH.as_posix())
    if route_warning:
        result.warnings.append(route_warning)

    if not spec.fields:
        result.warnings.append(
            f"Aucun champ public affichable détecté pour {spec.entity}."
        )

    return result


def make_public_show(
    entity_name: str,
    *,
    entities_root: Path | None = None,
    output_root: Path | None = None,
) -> MakePublicShowResult:
    project_root = (output_root or Path.cwd()).resolve()
    definition = load_public_list_definition(
        entity_name,
        entities_root=entities_root or project_root / ENTITIES_ROOT,
    )
    spec = build_public_list_spec(definition)
    result = MakePublicShowResult(spec=spec)

    template_path = project_root / spec.show_template_path
    template_path.parent.mkdir(parents=True, exist_ok=True)
    if template_path.exists():
        result.preserved.append(spec.show_template_path.as_posix())
    else:
        template_path.write_text(build_public_show_template(spec), encoding="utf-8")
        result.created.append(spec.show_template_path.as_posix())

    controller_changed, controller_warning = _ensure_show_controller(
        project_root / spec.controller_path,
        spec,
    )
    if controller_changed:
        result.created.append(spec.controller_path.as_posix())
    else:
        result.preserved.append(spec.controller_path.as_posix())
    if controller_warning:
        result.warnings.append(controller_warning)
        result.warnings.append(
            f"Route non ajoutée automatiquement tant que le contrôleur est à compléter : {ROUTES_PATH.as_posix()}"
        )
        result.preserved.append(ROUTES_PATH.as_posix())
    else:
        route_changed, route_warning = _ensure_show_route(project_root / ROUTES_PATH, spec)
        if route_changed:
            result.created.append(ROUTES_PATH.as_posix())
        else:
            result.preserved.append(ROUTES_PATH.as_posix())
        if route_warning:
            result.warnings.append(route_warning)

    if not spec.fields:
        result.warnings.append(
            f"Aucun champ public affichable détecté pour {spec.entity}."
        )

    return result


def print_result(result: MakePublicListResult) -> None:
    spec = result.spec
    print(f"Liste publique générée : {spec.entity}")
    print(f"Route : {spec.route_path}")
    print(f"Template : {spec.template_path.as_posix()}")
    print(f"Contrôleur : {spec.controller_path.as_posix()}")
    for path in result.created:
        print(out.created(path))
    for path in result.preserved:
        print(out.preserved(path))
    for warning in result.warnings:
        print(out.warn(warning))


def print_show_result(result: MakePublicShowResult) -> None:
    spec = result.spec
    print(f"Fiche publique générée : {spec.entity}")
    print(f"Route : {spec.show_route_path}")
    print(f"Template : {spec.show_template_path.as_posix()}")
    print(f"Contrôleur : {spec.controller_path.as_posix()}")
    for path in result.created:
        print(out.created(path))
    for path in result.preserved:
        print(out.preserved(path))
    for warning in result.warnings:
        print(out.warn(warning))


def main(args: list[str], *, root: Path | None = None) -> MakePublicListResult:
    if len(args) != 1:
        raise SystemExit("Usage : forge make:public-list <Entite>")
    project_root = root or Path.cwd()
    try:
        result = make_public_list(
            args[0],
            entities_root=project_root / ENTITIES_ROOT,
            output_root=project_root,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1) from exc
    print_result(result)
    return result


def show_main(args: list[str], *, root: Path | None = None) -> MakePublicShowResult:
    if len(args) != 1:
        raise SystemExit("Usage : forge make:public-show <Entite>")
    project_root = root or Path.cwd()
    try:
        result = make_public_show(
            args[0],
            entities_root=project_root / ENTITIES_ROOT,
            output_root=project_root,
        )
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        print(out.error(str(exc)))
        raise SystemExit(1) from exc
    print_show_result(result)
    return result
