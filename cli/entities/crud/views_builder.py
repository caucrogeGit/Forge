# pyright: strict
# pyright: reportPrivateUsage=false
"""Views builders for the CRUD generator (all build_*_view and build_*_partial functions)."""

from __future__ import annotations
from typing import Any

from cli.entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from cli.entities.crud.utils import (
    _filter_fields,
    _humanize,
    _is_bool_sql,
    _is_textarea,
    _html_input_type,
    _media_form_fields,
    _non_pk_fields,
    _pk_field,
    _relation_by_field,
    _to_snake,
)


def build_form_errors_partial() -> str:
    return """\
{% if form and form.errors %}
<div class="border bg-red-100 border-red-400 text-red-800 px-4 py-3 rounded mb-4">
    <ul class="list-disc list-inside">
        {% for field, messages in form.errors.items() %}
            {% for message in messages %}
                <li>{{ message }}</li>
            {% endfor %}
        {% endfor %}
    </ul>
</div>
{% endif %}
"""


def build_index_view(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
    rbac: dict[str, Any] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    rel_by_field = _relation_by_field(relations)
    perms = (rbac or {}).get("permissions", {})
    create_perm = perms.get("create")

    filter_flds = _filter_fields(definition, relations)
    _filters_loop = (
        "{% for key, val in pagination.filters.items() %}"
        "{% if val is not none and val != '' %}"
        "&amp;{{ key }}={{ val | urlencode }}"
        "{% endif %}{% endfor %}"
    )
    _nouveau_btn = [
        f"    {{{{ button(label='Nouveau {snake}', variant='primary', href='/{snake}/new') }}}}",
    ]
    if create_perm:
        _nouveau_btn = [f"    {{% if can('{create_perm}') %}}"] + _nouveau_btn + ["    {% endif %}"]
    lines: list[str] = [
        '{% extends "layouts/base.html" %}',
        "{% block content %}",
        '{% from "components/ui.html" import button, flash_messages %}',
        "{{ flash_messages(flash) }}",
        '<div class="flex justify-between items-center mb-6">',
        f'    <h1 class="text-2xl font-bold text-gray-800">Liste des {plural}</h1>',
        *_nouveau_btn,
        "</div>",
        "",
        f'<form method="get" action="/{snake}"',
        f'      hx-get="/{snake}" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true"',
        '      class="mb-4 flex gap-2 items-center flex-wrap">',
        '    <input type="search" name="q" value="{{ pagination.q }}"',
        "           placeholder=\"{{ trans('common.search') }}…\"",
        '           class="border border-gray-300 rounded px-3 py-1.5 text-sm w-64 focus:outline-none focus:ring-2 focus:ring-blue-400">',
    ]
    for ff in filter_flds:
        fname = ff["name"]
        relation = rel_by_field.get(fname)
        label = _humanize(fname)
        if relation is not None:
            lines += [
                f'    <select name="{fname}"',
                '            class="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">',
                f'        <option value="">Tous les {relation.target_entity}</option>',
                f"        {{% for option in relation_filters.{fname}.options %}}",
                f"        <option value=\"{{{{ option.id }}}}\" {{{{ 'selected' if pagination.filters.{fname}|string == option.id|string else '' }}}}>{{{{ option.label }}}}</option>",
                "        {% endfor %}",
                "    </select>",
            ]
        elif _is_bool_sql(ff.get("sql_type", "")):
            lines += [
                f'    <select name="{fname}"',
                '            class="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">',
                '        <option value="">Tous</option>',
                f"        <option value=\"1\" {{{{ 'selected' if pagination.filters.{fname} == '1' }}}}>{{{{ trans('common.yes') }}}}</option>",
                f"        <option value=\"0\" {{{{ 'selected' if pagination.filters.{fname} == '0' }}}}>{{{{ trans('common.no') }}}}</option>",
                "    </select>",
            ]
        else:
            lines.append(
                f'    <input type="text" name="{fname}" value="{{{{ pagination.filters.{fname} }}}}"'
                f' placeholder="{label}…"'
                ' class="border border-gray-300 rounded px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400">'
            )
    lines += [
        '    <button type="submit"',
        '            class="bg-gray-100 text-gray-800 text-sm px-3 py-1.5 rounded font-medium hover:bg-gray-200">',
        "        {{ trans('common.search') }}</button>",
        "    {% if pagination.q or pagination.filters %}",
        f'    <a href="/{snake}"',
        f'       hx-get="/{snake}" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true"',
        '       class="text-sm text-gray-500 hover:underline">Réinitialiser</a>',
        "    {% endif %}",
        "</form>",
        "",
        '<div class="mb-2">',
        (
            f'    <a href="/{snake}/export-csv'
            "?q={{ pagination.q | urlencode }}"
            "&amp;sort={{ pagination.sort }}"
            "&amp;direction={{ pagination.direction }}"
            "{% for key, val in pagination.filters.items() %}"
            "{% if val %}&amp;{{ key }}={{ val | urlencode }}{% endif %}"
            '{% endfor %}"'
        ),
        '       class="text-sm text-blue-600 hover:underline">Exporter CSV</a>',
        "</div>",
        "",
        '<div id="crud-results">',
        f'    {{% include "{snake}/_results.html" %}}',
        "</div>",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def build_results_partial(definition: dict[str, Any]) -> str:
    snake = _to_snake(definition["entity"])
    return "\n".join([
        f'{{% include "{snake}/_table.html" %}}',
        f'{{% include "{snake}/_pagination.html" %}}',
    ]) + "\n"


def _render_table_headers(
    non_pk: list[dict[str, Any]],
    rel_by_field: dict[str, CrudManyToOneRelation],
    many_to_many_relations: list[CrudManyToManyRelation] | None,
    filters_loop: str,
) -> list[str]:
    """En-têtes de colonnes triables + colonnes many-to-many + actions
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_table_partial` à iso-sortie.
    """
    lines: list[str] = []
    for f in non_pk:
        fname = f["name"]
        relation = rel_by_field.get(fname)
        label = relation.target_entity if relation else _humanize(fname)
        _sort_url = (
            f"?sort={fname}"
            f"{{% if pagination.sort == '{fname}' %}}"
            f"&amp;direction={{{{ 'desc' if pagination.direction == 'asc' else 'asc' }}}}"
            f"{{% else %}}&amp;direction=asc{{% endif %}}"
            f"{{% if pagination.q %}}&amp;q={{{{ pagination.q | urlencode }}}}{{% endif %}}"
            + filters_loop
        )
        lines.append(
            f'                <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">'
            f'<a href="{_sort_url}"'
            f' hx-get="{_sort_url}"'
            f' hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true">'
            f"{label}"
            f"{{% if pagination.sort == '{fname}' %}} {{{{ '↑' if pagination.direction == 'asc' else '↓' }}}}{{% endif %}}"
            f"</a></th>"
        )
    for relation in many_to_many_relations or []:
        lines.append(
            f'                <th class="px-4 py-3 text-left text-sm font-semibold text-gray-600">{_humanize(relation.target_entity)}</th>'
        )
    lines.append(
        "                <th class=\"px-4 py-3 text-right text-sm font-semibold text-gray-600\">{{ trans('crud.actions') }}</th>"
    )
    return lines


def _render_table_row(
    snake: str,
    pk_col: str,
    non_pk: list[dict[str, Any]],
    rel_by_field: dict[str, CrudManyToOneRelation],
    many_to_many_relations: list[CrudManyToManyRelation] | None,
    edit_perm: str | None,
    delete_perm: str | None,
    list_query: str,
) -> list[str]:
    """Contenu d'une ligne de table : case de sélection, cellules et actions
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_table_partial` à iso-sortie.
    """
    lines: list[str] = []
    # Colonne checkbox de sélection groupée (référence le formulaire bulk-delete-form via form=)
    _checkbox_input = f'<input type="checkbox" name="ids" value="{{{{ {snake}.{pk_col} }}}}" form="bulk-delete-form" class="rounded">'
    if delete_perm:
        lines += [
            f"                {{% if can('{delete_perm}') %}}",
            f'                <td class="px-4 py-3">{_checkbox_input}</td>',
            "                {% else %}",
            '                <td class="px-4 py-3"></td>',
            "                {% endif %}",
        ]
    else:
        lines.append(f'                <td class="px-4 py-3">{_checkbox_input}</td>')
    for f in non_pk:
        fname = f["name"]
        relation = rel_by_field.get(fname)
        display_attr = f"{fname}_label" if relation else f["column"]
        lines.append(
            f'                <td class="px-4 py-3 text-gray-800">'
            f"{{{{ {snake}.{display_attr} }}}}</td>"
        )
    for relation in many_to_many_relations or []:
        lines += [
            f"                {{% set _{relation.field_name}_labels = {relation.list_context_key}.get({snake}.{pk_col}, []) %}}",
            f'                <td class="px-4 py-3 text-gray-800">{{{{ _{relation.field_name}_labels | join(", ") if _{relation.field_name}_labels else "—" }}}}</td>',
        ]
    _edit_link = [
        f'                    <a href="/{snake}/edit/{{{{ {snake}.{pk_col} }}}}"',
        "                       class=\"text-sm text-blue-600 hover:underline\">{{ trans('crud.edit') }}</a>",
    ]
    if edit_perm:
        _edit_link = [f"                    {{% if can('{edit_perm}') %}}"] + _edit_link + ["                    {% endif %}"]
    _delete_form = [
        f'                    <form method="post" action="/{snake}/destroy/{{{{ {snake}.{pk_col} }}}}{list_query}"',
        f'                          hx-post="/{snake}/destroy/{{{{ {snake}.{pk_col} }}}}{list_query}" hx-target="#crud-results" hx-swap="innerHTML" hx-confirm="{{{{ trans(\'crud.confirm_delete\') }}}}"',
        '                          style="display:inline" onsubmit="return confirm(\'{{ trans("crud.confirm_delete") }}\')">',
        '                        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '                        <button type="submit"',
        "                            class=\"text-sm font-medium text-red-600 hover:text-red-800\">{{ trans('crud.delete') }}</button>",
        "                    </form>",
    ]
    if delete_perm:
        _delete_form = [f"                    {{% if can('{delete_perm}') %}}"] + _delete_form + ["                    {% endif %}"]
    lines += [
        '                <td class="px-4 py-3 text-right space-x-2">',
        f'                    <a href="/{snake}/show/{{{{ {snake}.{pk_col} }}}}"',
        "                       class=\"text-sm text-blue-600 hover:underline\">{{ trans('crud.show') }}</a>",
        *_edit_link,
        *_delete_form,
        "                </td>",
    ]
    return lines


def build_table_partial(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
    rbac: dict[str, Any] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_col = pk["column"]
    non_pk = _non_pk_fields(definition)
    rel_by_field = _relation_by_field(relations)
    perms = (rbac or {}).get("permissions", {})
    edit_perm = perms.get("edit")
    delete_perm = perms.get("delete")

    _filters_loop = (
        "{% for key, val in pagination.filters.items() %}"
        "{% if val is not none and val != '' %}"
        "&amp;{{ key }}={{ val | urlencode }}"
        "{% endif %}{% endfor %}"
    )
    _list_query = (
        "?page={{ pagination.page }}"
        "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}"
        "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}"
        + _filters_loop
    )

    # Formulaire de suppression groupée (avant la table, référencé par form= sur les cases)
    _bulk_form_lines: list[str] = [
        '<form id="bulk-delete-form"',
        f'      method="post" action="/{snake}/bulk-delete"',
        '      class="mb-3 flex items-center gap-3">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        '    <button type="submit"',
        '            class="bg-red-100 text-red-700 text-sm px-3 py-1.5 rounded font-medium hover:bg-red-200">',
        '        Supprimer la sélection',
        '    </button>',
        '</form>',
    ]
    if delete_perm:
        _bulk_form_lines = [f"{{% if can('{delete_perm}') %}}"] + _bulk_form_lines + ["{% endif %}"]

    lines: list[str] = [
        *_bulk_form_lines,
        f"{{% if {plural} %}}",
        '<div class="bg-white shadow rounded overflow-hidden">',
        "    <table class=\"w-full\">",
        "        <thead class=\"bg-gray-50 border-b\">",
        "            <tr>",
        '                <th class="px-4 py-3 w-10"></th>',
    ]
    lines += _render_table_headers(non_pk, rel_by_field, many_to_many_relations, _filters_loop)
    lines += [
        "            </tr>",
        "        </thead>",
        "        <tbody class=\"divide-y divide-gray-100\">",
        f"            {{% for {snake} in {plural} %}}",
        "            <tr class=\"hover:bg-gray-50\">",
    ]
    lines += _render_table_row(
        snake, pk_col, non_pk, rel_by_field, many_to_many_relations,
        edit_perm, delete_perm, _list_query,
    )
    lines += [
        "            </tr>",
        "            {% endfor %}",
        "        </tbody>",
        "    </table>",
        "</div>",
        "",
        "{% else %}",
        '<div class="rounded-xl border border-dashed border-gray-300 bg-white p-6 text-center text-gray-600">',
        '    {% if empty_context == "search" %}',
        "    {{ trans('crud.empty_search') }}",
        '    {% elif empty_context == "filters" %}',
        "    {{ trans('crud.empty_filters') }}",
        '    {% elif empty_context == "search_filters" %}',
        "    {{ trans('crud.empty_search_filters') }}",
        "    {% else %}",
        "    {{ trans('crud.empty') }}",
        "    {% endif %}",
        "</div>",
        "{% endif %}",
    ]
    return "\n".join(lines) + "\n"


def build_pagination_partial(definition: dict[str, Any]) -> str:
    _filters_loop = (
        "{% for key, val in pagination.filters.items() %}"
        "{% if val is not none and val != '' %}"
        "&amp;{{ key }}={{ val | urlencode }}"
        "{% endif %}{% endfor %}"
    )
    _prev_url = (
        "?page={{ pagination.page - 1 }}"
        "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}"
        "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}"
        + _filters_loop
    )
    _next_url = (
        "?page={{ pagination.page + 1 }}"
        "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}"
        "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}"
        + _filters_loop
    )

    lines: list[str] = [
        "{% if pagination.nb_pages > 1 %}",
        '<div class="flex items-center gap-2 mt-4 text-sm">',
        "    {% if pagination.has_prev %}",
        f'    <a href="{_prev_url}"',
        f'       hx-get="{_prev_url}" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true"',
        '       class="px-3 py-1.5 bg-white border border-gray-200 rounded hover:bg-gray-50">← Préc.</a>',
        "    {% endif %}",
        '    <span class="text-gray-500">Page {{ pagination.page }} / {{ pagination.nb_pages }}</span>',
        "    {% if pagination.has_next %}",
        f'    <a href="{_next_url}"',
        f'       hx-get="{_next_url}" hx-target="#crud-results" hx-swap="innerHTML" hx-push-url="true"',
        '       class="px-3 py-1.5 bg-white border border-gray-200 rounded hover:bg-gray-50">Suiv. →</a>',
        "    {% endif %}",
        "</div>",
        "{% endif %}",
    ]
    return "\n".join(lines) + "\n"


def build_show_view(
    definition: dict[str, Any],
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
    rbac: dict[str, Any] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    pk = _pk_field(definition)
    pk_col = pk["column"]
    non_pk = _non_pk_fields(definition)
    perms = (rbac or {}).get("permissions", {})
    edit_perm = perms.get("edit")
    delete_perm = perms.get("delete")

    _edit_btn = [
        f"        {{{{ button(label=trans('crud.edit'), variant='primary', href='/{snake}/edit/' ~ {snake}.{pk_col}) }}}}",
    ]
    if edit_perm:
        _edit_btn = [f"        {{% if can('{edit_perm}') %}}"] + _edit_btn + ["        {% endif %}"]

    lines: list[str] = [
        '{% extends "layouts/base.html" %}',
        "{% block content %}",
        '{% from "components/ui.html" import button, flash_messages %}',
        "{{ flash_messages(flash) }}",
        '<div class="flex justify-between items-center mb-6">',
        f'    <h1 class="text-2xl font-bold text-gray-800">Détail {snake}</h1>',
        '    <div class="space-x-2">',
        *_edit_btn,
        f"        <a href=\"/{snake}\" class=\"text-gray-600 hover:underline\">← {{{{ trans('common.back') }}}}</a>",
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
    for relation in many_to_many_relations or []:
        label = _humanize(relation.target_entity)
        lines += [
            "    <div>",
            f'        <p class="text-sm text-gray-500">{label}</p>',
            f"        {{% if {relation.show_context_key} %}}",
            f'        <p class="text-gray-800">{{{{ {relation.show_context_key} | join(", ") }}}}</p>',
            "        {% else %}",
            f'        <p class="text-gray-400 italic">Aucun {relation.target_entity}</p>',
            "        {% endif %}",
            "    </div>",
        ]
    for entry in _media_form_fields(definition):
        if entry.get("multiple", False):
            mname = entry["name"]
            mlabel = entry.get("label") or _humanize(mname)
            lines += [
                "    <div>",
                f'        <p class="text-sm text-gray-500">{mlabel}</p>',
                f"        {{% if {mname}_media_list %}}",
                '        <div class="flex flex-wrap gap-2 mt-1">',
                f"            {{% for _m in {mname}_media_list %}}",
            ]
            if entry["field"] == "image":
                lines += [
                    '            <img src="{{ _m.thumbnail_url or _m.url }}"',
                    f'                 alt="{{{{ _m.alt_text or \'{mlabel}\' }}}}"',
                    '                 class="h-24 rounded">',
                ]
            else:
                lines.append(
                    '            <a href="{{ _m.url }}" class="text-blue-600 hover:underline text-sm">Fichier</a>'
                )
            lines += [
                "            {% endfor %}",
                "        </div>",
                "        {% else %}",
                '        <p class="text-gray-400 italic">Aucune image</p>',
                "        {% endif %}",
                "    </div>",
            ]
            continue
        mname = entry["name"]
        mlabel = entry.get("label") or _humanize(mname)
        lines.append("    <div>")
        lines.append(f'        <p class="text-sm text-gray-500">{mlabel}</p>')
        if entry["field"] == "image":
            lines += [
                f"        {{% if {mname}_media %}}",
                f'        <img src="{{{{ {mname}_media.thumbnail_url or {mname}_media.url }}}}"',
                f'             alt="{{{{ {mname}_media.alt_text or \'{mlabel}\' }}}}"',
                '             class="h-32 rounded">',
                "        {% else %}",
                '        <p class="text-gray-400 italic">Aucune image</p>',
                "        {% endif %}",
            ]
        else:
            lines += [
                f"        {{% if {mname}_media %}}",
                f'        <a href="{{{{ {mname}_media.url }}}}" class="text-blue-600 hover:underline">Voir le fichier</a>',
                "        {% else %}",
                '        <p class="text-gray-400 italic">Aucun fichier</p>',
                "        {% endif %}",
            ]
        lines.append("    </div>")
    _delete_form = [
        f'<form method="post" action="/{snake}/destroy/{{{{ {snake}.{pk_col} }}}}" class="mt-4" onsubmit="return confirm(\'{{{{ trans("crud.confirm_delete") }}}}\')">',
        '    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        "    {{ button(label=trans('crud.delete'), variant='danger', type='submit') }}",
        "</form>",
    ]
    if delete_perm:
        _delete_form = [f"{{% if can('{delete_perm}') %}}"] + _delete_form + ["{% endif %}"]
    lines += [
        "</div>",
        "",
        *_delete_form,
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def _render_form_fields(
    non_pk: list[dict[str, Any]],
    relations_by_field: dict[str, CrudManyToOneRelation],
) -> list[str]:
    """Champs du formulaire (select de relation, textarea, case, input)
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_form_view` à iso-sortie.
    """
    lines: list[str] = []
    for f in non_pk:
        fname = f["name"]
        label = _humanize(fname)
        python_type = f.get("python_type", "str")
        relation = relations_by_field.get(fname)

        if relation is not None:
            # Le select porte sur l'entité liée : libellé sans le suffixe _id.
            rel_label = _humanize(fname[:-3] if fname.endswith("_id") else fname)
            lines.append(
                f"        {{{{ select_field(name='{fname}', label='{rel_label}', "
                f"options=form.options.{relation.choices_key}, selected=form.value('{fname}'), "
                f"error=form.error('{fname}')) }}}}"
            )
        elif _is_textarea(f):
            lines.append(
                f"        {{{{ textarea_field(name='{fname}', label='{label}', "
                f"value=form.value('{fname}'), error=form.error('{fname}')) }}}}"
            )
        elif python_type == "bool":
            lines.append(
                f"        {{{{ checkbox(name='{fname}', label='{label}', checked=form.value('{fname}')) }}}}"
            )
        else:
            html_type = _html_input_type(f)
            lines.append(
                f"        {{{{ field(name='{fname}', label='{label}', type='{html_type}', "
                f"value=form.value('{fname}'), error=form.error('{fname}')) }}}}"
            )
    return lines


def _render_form_m2m(
    many_to_many_relations: list[CrudManyToManyRelation] | None,
) -> list[str]:
    """Selects multiples des relations many-to-many du formulaire
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_form_view` à iso-sortie.
    """
    lines: list[str] = []
    _select_cls = 'class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"'
    for relation in many_to_many_relations or []:
        label = _humanize(relation.target_entity)
        lines += [
            "        <div>",
            f'            <label class="block text-sm font-medium text-gray-700">{label}</label>',
            "            <select",
            f'                name="{relation.field_name}"',
            "                multiple",
            f"                {_select_cls}",
            "            >",
            f"                {{% for value, label in {relation.choices_key} %}}",
            f"                <option value=\"{{{{ value }}}}\" {{{{ 'selected' if value in {relation.selected_key} else '' }}}}>{{{{ label }}}}</option>",
            "                {% endfor %}",
            "            </select>",
            "        </div>",
        ]
    return lines


def _render_form_media(media_entries: list[dict[str, Any]]) -> list[str]:
    """Champs de média (upload simple/galerie, image/fichier) du formulaire
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_form_view` à iso-sortie.
    """
    lines: list[str] = []
    _file_cls = 'class="mt-1 w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"'
    for entry in media_entries:
        mname = entry["name"]
        mlabel = entry.get("label") or _humanize(mname)
        input_lines = [
            "        <div>",
            f'            <label class="block text-sm font-medium text-gray-700">{mlabel}</label>',
        ]
        if entry.get("multiple", False):
            if entry["field"] == "image":
                input_lines += [
                    f"            {{% if {mname}_media_list %}}",
                    '            <div class="flex flex-wrap gap-2 mb-2">',
                    f"                {{% for _m in {mname}_media_list %}}",
                    '                <div>',
                    '                <img src="{{ _m.thumbnail_url or _m.url }}"',
                    f'                     alt="{{{{ _m.alt_text or \'{mlabel}\' }}}}"',
                    '                     class="h-20 rounded">',
                    '                <label class="flex items-center gap-1 text-xs text-gray-600 mt-1">',
                    f'                    <input type="checkbox" name="_delete_media_{mname}" value="{{{{ _m.id }}}}">',
                    "                    {{ trans('crud.delete') }}",
                    "                </label>",
                    f'                <input type="number" name="_media_position_{mname}_{{{{ _m.id }}}}" value="{{{{ _m.position }}}}" min="0" class="mt-1 w-16 border border-gray-300 rounded px-1 py-0.5 text-xs">',
                    f'                <input type="text" name="_media_alt_{mname}_{{{{ _m.id }}}}" value="{{{{ _m.alt_text or \'\' }}}}" placeholder="Texte alternatif" class="mt-1 w-full border border-gray-300 rounded px-1 py-0.5 text-xs">',
                    '                </div>',
                    "                {% endfor %}",
                    "            </div>",
                    "            {% endif %}",
                    f'            <input type="text" name="_media_alt_{mname}_new" placeholder="Texte alternatif du nouveau média" class="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">',
                ]
        elif entry["field"] == "image":
                input_lines += [
                    f"            {{% if {mname}_media %}}",
                    '            <div class="mb-2">',
                    f'                <img src="{{{{ {mname}_media.thumbnail_url or {mname}_media.url }}}}"',
                    f'                     alt="{{{{ {mname}_media.alt_text or \'{mlabel}\' }}}}"',
                    '                     class="h-24 rounded">',
                    '                <p class="text-xs text-gray-500 mt-1">Un nouveau fichier remplacera l\'image actuelle.</p>',
                    '                <label class="flex items-center gap-2 mt-1 text-sm text-gray-600">',
                    f'                    <input type="checkbox" name="_delete_media_{mname}" value="1">',
                    "                    Supprimer le média actuel",
                    "                </label>",
                    "            </div>",
                    "            {% endif %}",
                    f'            <input type="text" name="_media_alt_{mname}" value="{{{{ ({mname}_media.alt_text or \'\') if {mname}_media else \'\' }}}}" placeholder="Texte alternatif" class="mt-1 w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">',
                ]
        else:
                input_lines += [
                    f"            {{% if {mname}_media %}}",
                    '            <div class="mb-2">',
                    f'                <a href="{{{{ {mname}_media.url }}}}" class="text-blue-600 hover:underline text-sm">Voir le fichier actuel</a>',
                    '                <p class="text-xs text-gray-500 mt-1">Un nouveau fichier remplacera le fichier actuel.</p>',
                    '                <label class="flex items-center gap-2 mt-1 text-sm text-gray-600">',
                    f'                    <input type="checkbox" name="_delete_media_{mname}" value="1">',
                    "                    Supprimer le média actuel",
                    "                </label>",
                    "            </div>",
                    "            {% endif %}",
                ]
        input_lines += [
            "            <input",
            '                type="file"',
            f'                name="{mname}"',
        ]
        if entry.get("multiple", False):
            input_lines.append('                multiple')
        if entry["field"] == "image":
            input_lines.append('                accept="image/*"')
        input_lines += [
            f"                {_file_cls}",
            "            >",
            f"            {{% if form.has_error('{mname}') %}}",
            f"            <p class=\"text-red-600 text-sm mt-1\">{{{{ form.error('{mname}') }}}}</p>",
            "            {% endif %}",
            "        </div>",
        ]
        lines += input_lines
    return lines


def build_form_view(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    non_pk = _non_pk_fields(definition)
    relations_by_field = _relation_by_field(relations)
    media_entries = _media_form_fields(definition)

    form_tag = (
        '    <form method="post" action="{{ action }}" enctype="multipart/form-data" class="space-y-4">'
        if media_entries else
        '    <form method="post" action="{{ action }}" class="space-y-4">'
    )

    lines: list[str] = [
        '{% extends "layouts/base.html" %}',
        "{% block content %}",
        '{% from "components/ui.html" import button, flash_messages %}',
        '{% from "components/forms.html" import field, textarea_field, select_field, checkbox %}',
        "{{ flash_messages(flash) }}",
        '<div class="flex justify-between items-center mb-6">',
        '    <h1 class="text-2xl font-bold text-gray-800">{{ titre }}</h1>',
        f"    <a href=\"/{snake}\" class=\"text-gray-600 hover:underline\">← {{{{ trans('common.back') }}}}</a>",
        "</div>",
        "",
        '{% include "partials/form_errors.html" %}',
        "",
        '<div class="bg-white shadow rounded p-6">',
        form_tag,
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
    ]

    lines += _render_form_fields(non_pk, relations_by_field)
    lines += _render_form_m2m(many_to_many_relations)
    lines += _render_form_media(media_entries)

    lines += [
        '        <div class="flex gap-4 pt-2">',
        "            {{ button(label=trans('common.save'), variant='primary', type='submit') }}",
        f"            {{{{ button(label=trans('common.cancel'), variant='secondary', href='/{snake}') }}}}",
        "        </div>",
        "    </form>",
        "</div>",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"


def build_bulk_delete_confirm_view(definition: dict[str, Any]) -> str:
    """Génère le template de confirmation de suppression groupée."""
    entity = definition["entity"]
    snake = _to_snake(entity)

    lines: list[str] = [
        '{% extends "layouts/base.html" %}',
        "{% block content %}",
        '{% from "components/ui.html" import flash_messages %}',
        "{{ flash_messages(flash) }}",
        '<div class="max-w-xl mx-auto">',
        '    <h1 class="text-2xl font-bold text-gray-800 mb-4">Confirmer la suppression</h1>',
        '    <div class="bg-red-50 border border-red-200 rounded-lg p-6 mb-6">',
        "        <p class=\"text-gray-800 mb-2\">",
        "            Vous êtes sur le point de supprimer",
        "            <strong>{{ count }} élément{{ 's' if count > 1 else '' }}</strong>.",
        "        </p>",
        '        <p class="text-red-700 font-medium">Cette action est définitive et irréversible.</p>',
        "    </div>",
        f'    <form method="post" action="/{snake}/bulk-delete-confirm">',
        '        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">',
        "        {% for id in ids %}",
        '        <input type="hidden" name="ids" value="{{ id }}">',
        "        {% endfor %}",
        '        <div class="flex gap-4">',
        '            <button type="submit"',
        '                    class="bg-red-600 text-white text-sm px-4 py-2 rounded font-medium hover:bg-red-700">',
        "                Confirmer la suppression",
        "            </button>",
        f'            <a href="/{snake}"',
        '               class="bg-gray-100 text-gray-800 text-sm px-4 py-2 rounded font-medium hover:bg-gray-200">',
        "                Annuler",
        "            </a>",
        "        </div>",
        "    </form>",
        "</div>",
        "{% endblock %}",
    ]
    return "\n".join(lines) + "\n"
