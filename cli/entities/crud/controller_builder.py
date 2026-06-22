"""Controller builder for the CRUD generator."""

from __future__ import annotations

from cli.entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from cli.entities.crud.utils import (
    _filter_fields,
    _humanize,
    _is_bool_sql,
    _is_generated,
    _media_form_fields,
    _non_pk_fields,
    _pk_field,
    _relation_by_field,
    _to_snake,
)
from cli.entities.crud.context import _with_permission


def _media_upload_call(mfield: str, var: str, variants) -> str:
    """Expression d'upload générée pour un champ média.

    CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : les champs **image** passent par
    le chemin image-aware de l'opt-in (`save_image_upload`, vérification de
    contenu + variantes) ; les autres fichiers utilisent le `save_upload`
    **générique** du core.
    """
    if mfield == "image":
        return f'save_image_upload({var}, "images", variants={variants})'
    return f'save_upload({var}, "documents")'
from cli.entities.crud.relations_loader import (
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)


def build_controller(
    definition: dict,
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_name = pk["name"]
    pk_col = pk["column"]
    non_pk = _non_pk_fields(definition)
    # Champs slug auto-générés : (nom, champ source) — calculés à la création.
    generated_fields = [(f["name"], f["source"]) for f in non_pk if _is_generated(f)]
    allowed_sort_keys = [f["name"] for f in non_pk] + [pk_name]
    allowed_sort_keys_repr = "{" + ", ".join(f'"{key}"' for key in allowed_sort_keys) + "}"
    choice_relations = _unique_choice_relations(relations)
    many_to_many_choice_relations = _unique_many_to_many_choice_relations(many_to_many_relations)
    choice_imports = [relation.choices_function for relation in choice_relations]
    for relation in many_to_many_choice_relations:
        if relation.choices_function not in choice_imports:
            choice_imports.append(relation.choices_function)
    many_to_many_imports: list[str] = []
    for relation in many_to_many_relations or []:
        many_to_many_imports.extend([
            relation.selected_function,
            relation.add_function,
            relation.sync_function,
            relation.list_labels_function,
            relation.show_labels_function,
        ])
    choice_options = relations or []

    ctrl_media_entries = _media_form_fields(definition)

    # RBAC — permissions optionnelles depuis la définition JSON
    _rbac_raw = (definition.get("rbac") or {}).get("permissions") or {}
    _rbac: dict[str, str] = {}
    if _rbac_raw:
        from forge_mvc_rbac import normalize_permission_code
        _rbac = {
            action: normalize_permission_code(code)
            for action, code in _rbac_raw.items()
            if isinstance(code, str) and code.strip()
        }

    lines: list[str] = [
        "import csv",
        "import io",
        "from core.http.request import Request",
        "from core.http.response import Response",
    ]
    if generated_fields:
        lines.append("from core.http.slug import slugify")
    if _rbac:
        lines.append("from forge_mvc_rbac import require_permission")
    lines += [
        "from core.mvc.controller import BaseController",
        "from core.mvc.view.pagination import Pagination",
        f"from mvc.models.{snake}_model import (",
        f"    get_{plural}, get_{snake}_by_id, add_{snake}, update_{snake}, delete_{snake}, bulk_delete_{plural},",
        f"    count_{plural}, find_{plural}_paginated, find_{plural}_for_export,",
    ]
    if choice_imports:
        lines.append(f"    {', '.join(choice_imports)},")
    if many_to_many_imports:
        lines.append(f"    {', '.join(many_to_many_imports)},")
    lines.extend([
        ")",
        f"from mvc.forms.{snake}_form import {entity}Form",
        "from mvc.helpers.flash import render_flash_html",
    ])
    if ctrl_media_entries:
        _has_single   = any(not e.get("multiple", False) for e in ctrl_media_entries)
        _has_multiple = any(e.get("multiple", False) for e in ctrl_media_entries)
        # CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : les champs image passent
        # par forge_mvc_images.save_image_upload (vérification + variantes) ; les
        # autres fichiers par le save_upload générique du core.
        _has_image = any(e.get("field") == "image" for e in ctrl_media_entries)
        _has_doc   = any(e.get("field") != "image" for e in ctrl_media_entries)
        if _has_doc:
            # FILES-CLI-RENAME-001 (ADR-019) : upload générique = forge-mvc-files.
            lines.append("from forge_mvc_files import save_upload")
        _img_helpers = ["attach_media_to_entity", "delete_media"]
        if _has_single:
            _img_helpers.append("get_cover_media")
        _img_helpers += ["list_media_for_entity", "update_media_alt_text"]
        if _has_multiple:
            _img_helpers.append("update_media_position")
        if _has_image:
            _img_helpers.append("save_image_upload")
        lines.append("from forge_mvc_images import " + ", ".join(_img_helpers))
    lines.extend([
        "",
        "",
        f"def _form_data_from_{snake}(record: dict) -> dict:",
        '    """Convertit les colonnes SQL vers les noms de champs du formulaire."""',
        "    return {",
    ])
    for f in non_pk:
        fname = f["name"]
        fcol = f["column"]
        lines.append(f'        "{fname}": record.get("{fcol}"),')
    lines.append("    }")
    lines.append("")
    if choice_options:
        lines.append("")
        lines.append(f"def _{snake}_form_options():")
        lines.append("    return {")
        for relation in choice_options:
            lines.append(f'        "{relation.choices_key}": {relation.choices_function}(),')
        lines.append("    }")
        lines.append("")
    lines.append("")
    lines.append("def _query_param(request, name, default=\"\"):")
    lines.append('    """Retourne le premier paramètre GET, au format parse_qs de Forge."""')
    lines.append("    values = request.params.get(name, [default])")
    lines.append("    return values[0] if values else default")
    lines.append("")
    lines.append("")
    lines.append("def _is_hx_request(request):")
    lines.append('    """Détecte une requête HTMX locale au CRUD généré."""')
    lines.append('    return request.headers.get("HX-Request", "").lower() == "true"')
    lines.append("")
    lines.append("")
    _rel_by_field = _relation_by_field(relations)
    _csv_cols = []
    for _f in non_pk:
        _fname = _f["name"]
        _rel = _rel_by_field.get(_fname)
        _header = _humanize(_fname)
        _row_key = f"{_fname}_label" if _rel else _f["column"]
        _csv_cols.append((_header, _row_key))
    lines.append(f"_CSV_COLS = {_csv_cols!r}")
    lines.append("")
    lines.append("")
    lines.append(f"class {entity}Controller(BaseController):")
    lines += [
        "",
        "    @staticmethod",
        "    def _parse_id(value):",
        "        try:",
        "            return int(value)",
        "        except (TypeError, ValueError):",
        "            return None",
        "",
        "    @staticmethod",
        "    def _parse_bulk_ids(request):",
        '        """Extrait, valide et déduplique les IDs du formulaire de suppression groupée."""',
        '        raw = request.body.get("ids", [])',
        "        if isinstance(raw, str):",
        "            raw = [raw]",
        "        valid = []",
        "        seen = set()",
        "        for v in (raw or []):",
        "            try:",
        "                item = int(v)",
        "            except (TypeError, ValueError):",
        "                continue",
        "            if item <= 0 or item in seen:",
        "                continue",
        "            seen.add(item)",
        "            valid.append(item)",
        "        return valid",
    ]
    if many_to_many_relations:
        lines += [
            "",
            "    @staticmethod",
            "    def _parse_many_ids(request, field_name):",
            "        raw = request.body.get(field_name, [])",
            "        values = raw if isinstance(raw, list) else ([raw] if raw else [])",
            "        selected = []",
            "        seen = set()",
            "        for value in values:",
            "            try:",
            "                item = int(value)",
            "            except (TypeError, ValueError):",
            "                continue",
            "            if item <= 0 or item in seen:",
            "                continue",
            "            seen.add(item)",
            "            selected.append(item)",
            "        return selected",
        ]

    # index
    filter_flds = _filter_fields(definition, relations)
    relation_filter_names = set(_relation_by_field(relations))
    list_context_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def _list_context(request):",
        '        q         = _query_param(request, "q").strip()',
        '        sort      = _query_param(request, "sort")',
        f"        if sort not in {allowed_sort_keys_repr}:",
        '            sort = ""',
        '        direction = _query_param(request, "direction", "desc")',
        '        if direction not in ("asc", "desc"):',
        '            direction = "asc"',
        "        limit  = 20",
    ]
    for ff in filter_flds:
        fname = ff["name"]
        if fname in relation_filter_names:
            list_context_lines.append(f'        {fname}_raw = _query_param(request, "{fname}").strip()')
            list_context_lines.append(f'        {fname}_f = ""')
            list_context_lines.append(f'        if {fname}_raw:')
            list_context_lines.append("            try:")
            list_context_lines.append(f"                {fname}_f = int({fname}_raw)")
            list_context_lines.append("            except (TypeError, ValueError):")
            list_context_lines.append(f'                {fname}_f = ""')
        else:
            list_context_lines.append(f'        {fname}_f = _query_param(request, "{fname}").strip()')
    if filter_flds:
        list_context_lines.append("        relation_filters = {}")
        filter_names = {ff["name"] for ff in filter_flds}
        for relation in relations or []:
            if relation.field_name in filter_names:
                list_context_lines.append(
                    f'        relation_filters["{relation.field_name}"] = {{'
                    f'"options": [{{"id": value, "label": label}} for value, label in {relation.choices_function}()]'
                    "}"
                )
        list_context_lines.append("        _filters = {}")
        for ff in filter_flds:
            fname = ff["name"]
            if _is_bool_sql(ff.get("sql_type", "")):
                list_context_lines.append(f'        if {fname}_f in ("0", "1"):')
                list_context_lines.append(f'            _filters["{fname}"] = {fname}_f')
            else:
                list_context_lines.append(f'        if {fname}_f != "":')
                list_context_lines.append(f'            _filters["{fname}"] = {fname}_f')
        list_context_lines.extend([
            f'        total    = count_{plural}(q or None, filters=_filters or None)',
            "        pagination_state = Pagination(request, total, limit)",
            "        limit = pagination_state.limit",
            "        offset = pagination_state.offset",
            '        empty_context = "search_filters" if q and _filters else ("search" if q else ("filters" if _filters else None))',
            f'        {plural} = find_{plural}_paginated(',
            "            q=q or None, sort=sort or None, direction=direction,",
            "            limit=limit, offset=offset, filters=_filters or None,",
            "        )",
        ])
        filters_dict = "{" + ", ".join(f'"{ff["name"]}": {ff["name"]}_f' for ff in filter_flds) + "}"
        list_context_lines.extend([
            "        pagination = pagination_state.to_dict()",
            '        pagination.update({',
            '            "q": q, "sort": sort, "direction": direction,',
            f'            "filters": {filters_dict},',
            "        })",
        ])
    else:
        list_context_lines.extend([
            "        relation_filters = {}",
            f'        total    = count_{plural}(q or None)',
            "        pagination_state = Pagination(request, total, limit)",
            "        limit = pagination_state.limit",
            "        offset = pagination_state.offset",
            '        empty_context = "search" if q else None',
            f'        {plural} = find_{plural}_paginated(',
            "            q=q or None, sort=sort or None, direction=direction,",
            "            limit=limit, offset=offset,",
            "        )",
            "        pagination = pagination_state.to_dict()",
            '        pagination.update({',
            '            "q": q, "sort": sort, "direction": direction,',
            '            "filters": {},',
            "        })",
        ])
    list_context_lines.extend([
        "        return {",
        f'                "{plural}": {plural},',
        "                \"pagination\": pagination,",
        "                \"empty_context\": empty_context,",
        "                \"relation_filters\": relation_filters,",
        "                \"flash_html\": render_flash_html(request),",
    ])
    for relation in many_to_many_relations or []:
        list_context_lines.append(
            f'                "{relation.list_context_key}": {relation.list_labels_function}([row["{pk_col}"] for row in {plural}]),'
        )
    list_context_lines.extend([
        "            }",
    ])
    lines += list_context_lines

    index_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def index(request: Request) -> Response:",
        f"        context = {entity}Controller._list_context(request)",
        f'        template = "{snake}/_results.html" if _is_hx_request(request) else "{snake}/index.html"',
        "        return BaseController.render(template, context=context, request=request)",
    ]
    lines += _with_permission(index_lines, _rbac.get("index"))

    # new
    new_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def new(request: Request) -> Response:",
        (
            f'        form = {entity}Form(**_{snake}_form_options())'
            if choice_options else
            f'        form = {entity}Form()'
        ),
        f'        return BaseController.render("{snake}/form.html",',
        '            context={',
        '                "form": form,',
        f'                "action": "/{snake}/create",',
        f'                "titre": "Nouveau {snake}",',
    ]
    for relation in many_to_many_relations or []:
        new_lines.append(f'                "{relation.choices_key}": {relation.choices_function}(),')
        new_lines.append(f'                "{relation.selected_key}": [],')
    new_lines += [
        "            },",
        "            request=request)",
    ]
    lines += _with_permission(new_lines, _rbac.get("create"))

    # create
    create_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def create(request: Request) -> Response:",
        (
            f'        form = {entity}Form.from_request(request, **_{snake}_form_options())'
            if choice_options else
            f'        form = {entity}Form.from_request(request)'
        ),
    ]
    for relation in many_to_many_relations or []:
        create_lines.append(
            f'        {relation.field_name} = {entity}Controller._parse_many_ids(request, "{relation.field_name}")'
        )
    create_lines += [
        "        if not form.is_valid():",
        f'            return BaseController.validation_error("{snake}/form.html",',
        '                context={',
        '                    "form": form,',
        f'                    "action": "/{snake}/create",',
        f'                    "titre": "Nouveau {snake}",',
    ]
    for relation in many_to_many_relations or []:
        create_lines.append(f'                    "{relation.choices_key}": {relation.choices_function}(),')
        create_lines.append(f'                    "{relation.selected_key}": {relation.field_name},')
    create_lines += [
        "                },",
        "                request=request)",
    ]
    # Slug auto-généré depuis son champ source (stable ensuite ; ADR-017).
    for _gen_name, _gen_source in generated_fields:
        create_lines.append(
            f'        form.cleaned_data["{_gen_name}"] = '
            f'slugify(form.cleaned_data["{_gen_source}"])'
        )
    if ctrl_media_entries:
        for entry in ctrl_media_entries:
            if not entry.get("multiple", False):
                continue
            mname = entry["name"]
            create_lines += [
                f'        _{mname}_files_raw = request.files.get("{mname}", [])',
                f'        _{mname}_files = _{mname}_files_raw if isinstance(_{mname}_files_raw, list) else ([_{mname}_files_raw] if _{mname}_files_raw else [])',
                f'        for _{mname}_f in _{mname}_files:',
                f'            if getattr(_{mname}_f, "filename", ""):',
                '                try:',
                f'                    form.fields["{mname}"].validate(_{mname}_f)',
                f'                except Exception as _{mname}_exc:',
                f'                    form.add_error("{mname}", getattr(_{mname}_exc, "messages", [str(_{mname}_exc)]))',
                f'                    return BaseController.validation_error("{snake}/form.html",',
                '                        context={',
                '                            "form": form,',
                f'                            "action": "/{snake}/create",',
                f'                            "titre": "Nouveau {snake}",',
            ]
            for relation in many_to_many_relations or []:
                create_lines.append(f'                            "{relation.choices_key}": {relation.choices_function}(),')
                create_lines.append(f'                            "{relation.selected_key}": {relation.field_name},')
            create_lines += [
                '                        },',
                '                        request=request)',
            ]
        media_names_repr = "{" + ", ".join(f'"{e["name"]}"' for e in ctrl_media_entries) + "}"
        create_lines += [
            f'        _media_keys = {media_names_repr}',
            '        _sql_data = {k: v for k, v in form.cleaned_data.items() if k not in _media_keys}',
            f'        created_id = add_{snake}(_sql_data)',
        ]
        for entry in ctrl_media_entries:
            mname = entry["name"]
            mrole = entry["role"]
            mfield = entry["field"]
            variants = entry.get("variants", False)
            _is_multiple = entry.get("multiple", False)
            _alt_key = f"_media_alt_{mname}_new" if _is_multiple else f"_media_alt_{mname}"
            if _is_multiple:
                create_lines += [
                    f'        _{mname}_alt = (request.body.get("{_alt_key}", [None])[0] or None)',
                    f'        for _{mname}_f in _{mname}_files:',
                    f'            if getattr(_{mname}_f, "filename", ""):',
                    f'                _saved_{mname} = {_media_upload_call(mfield, f"_{mname}_f", variants)}',
                    f'                attach_media_to_entity(_saved_{mname}, entity_name="{snake}", entity_id=created_id, role="{mrole}", position=0, alt_text=_{mname}_alt)',
                ]
            else:
                create_lines += [
                    f'        _{mname}_alt = (request.body.get("{_alt_key}", [None])[0] or None)',
                    f'        _{mname}_file = form.cleaned_data.get("{mname}")',
                    f'        if _{mname}_file and getattr(_{mname}_file, "filename", ""):',
                    f'            _saved_{mname} = {_media_upload_call(mfield, f"_{mname}_file", variants)}',
                    f'            attach_media_to_entity(_saved_{mname}, entity_name="{snake}", entity_id=created_id, role="{mrole}", position=0, alt_text=_{mname}_alt)',
                ]
    else:
        if many_to_many_relations:
            create_lines.append(f'        created_id = add_{snake}(form.cleaned_data)')
        else:
            create_lines.append(f'        add_{snake}(form.cleaned_data)')
    for relation in many_to_many_relations or []:
        create_lines.append(f'        {relation.add_function}(created_id, {relation.field_name})')
    create_lines.append(
        f'        return BaseController.redirect_with_flash(request, "/{snake}", "{entity} créé.")'
    )
    lines += _with_permission(create_lines, _rbac.get("store"))

    # show
    show_singles = [e for e in ctrl_media_entries if not e.get("multiple", False)]
    show_multiples = [e for e in ctrl_media_entries if e.get("multiple", False)]
    show_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def show(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route_params.get("id"))',
        f"        if {pk_name} is None:",
        "            return BaseController.not_found()",
        f'        {snake} = get_{snake}_by_id({pk_name})',
        f'        if {snake} is None:',
        "            return BaseController.not_found()",
    ]
    for entry in show_singles:
        mname = entry["name"]
        mrole = entry["role"]
        show_lines.append(
            f'        {mname}_media = get_cover_media("{snake}", {pk_name}, role="{mrole}")'
        )
    for entry in show_multiples:
        mname = entry["name"]
        mrole = entry["role"]
        show_lines.append(
            f'        {mname}_media_list = list_media_for_entity("{snake}", {pk_name}, role="{mrole}")'
        )
    for relation in many_to_many_relations or []:
        show_lines.append(f'        {relation.show_context_key} = {relation.show_labels_function}({pk_name})')
    ctx_items = [f'"{snake}": {snake}', '"flash_html": render_flash_html(request)']
    ctx_items += [f'"{relation.show_context_key}": {relation.show_context_key}' for relation in many_to_many_relations or []]
    ctx_items += [f'"{e["name"]}_media": {e["name"]}_media' for e in show_singles]
    ctx_items += [f'"{e["name"]}_media_list": {e["name"]}_media_list' for e in show_multiples]
    show_lines += [
        f'        return BaseController.render("{snake}/show.html",',
        f'            context={{{", ".join(ctx_items)}}},',
        "            request=request)",
    ]
    lines += _with_permission(show_lines, _rbac.get("show"))

    # edit
    edit_singles = show_singles  # same list
    edit_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def edit(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route_params.get("id"))',
        f"        if {pk_name} is None:",
        "            return BaseController.not_found()",
        f'        {snake} = get_{snake}_by_id({pk_name})',
        f'        if {snake} is None:',
        "            return BaseController.not_found()",
    ]
    for entry in edit_singles:
        mname = entry["name"]
        mrole = entry["role"]
        edit_lines.append(
            f'        {mname}_media = get_cover_media("{snake}", {pk_name}, role="{mrole}")'
        )
    for entry in show_multiples:
        mname = entry["name"]
        mrole = entry["role"]
        edit_lines.append(
            f'        {mname}_media_list = list_media_for_entity("{snake}", {pk_name}, role="{mrole}")'
        )
    edit_lines += [
        f'        return BaseController.render("{snake}/form.html",',
        '            context={',
        (
            f'                "form": {entity}Form(_form_data_from_{snake}({snake}), **_{snake}_form_options()),'
            if choice_options else
            f'                "form": {entity}Form(_form_data_from_{snake}({snake})),'
        ),
        f'                "action": f"/{snake}/update/{{{pk_name}}}",',
        f'                "titre": "Modifier {snake}",',
    ]
    for relation in many_to_many_relations or []:
        edit_lines.append(f'                "{relation.choices_key}": {relation.choices_function}(),')
        edit_lines.append(f'                "{relation.selected_key}": {relation.selected_function}({pk_name}),')
    for entry in edit_singles:
        mname = entry["name"]
        edit_lines.append(f'                "{mname}_media": {mname}_media,')
    for entry in show_multiples:
        mname = entry["name"]
        edit_lines.append(f'                "{mname}_media_list": {mname}_media_list,')
    edit_lines += [
        "            },",
        "            request=request)",
    ]
    lines += _with_permission(edit_lines, _rbac.get("edit"))

    # update
    update_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def update(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route_params.get("id"))',
        f"        if {pk_name} is None:",
        "            return BaseController.not_found()",
        (
            f'        form = {entity}Form.from_request(request, **_{snake}_form_options())'
            if choice_options else
            f'        form = {entity}Form.from_request(request)'
        ),
    ]
    for relation in many_to_many_relations or []:
        update_lines.append(
            f'        {relation.field_name} = {entity}Controller._parse_many_ids(request, "{relation.field_name}")'
        )
    update_lines += [
        "        if not form.is_valid():",
    ]
    for entry in show_singles:
        mname = entry["name"]
        mrole = entry["role"]
        update_lines.append(
            f'            {mname}_media = get_cover_media("{snake}", {pk_name}, role="{mrole}")'
        )
    for entry in show_multiples:
        mname = entry["name"]
        mrole = entry["role"]
        update_lines.append(
            f'            {mname}_media_list = list_media_for_entity("{snake}", {pk_name}, role="{mrole}")'
        )
    update_lines += [
        f'            return BaseController.validation_error("{snake}/form.html",',
        "                context={",
        '                    "form": form,',
        f'                    "action": f"/{snake}/update/{{{pk_name}}}",',
        f'                    "titre": "Modifier {snake}",',
    ]
    for relation in many_to_many_relations or []:
        update_lines.append(f'                    "{relation.choices_key}": {relation.choices_function}(),')
        update_lines.append(f'                    "{relation.selected_key}": {relation.field_name},')
    for entry in show_singles:
        mname = entry["name"]
        update_lines.append(f'                    "{mname}_media": {mname}_media,')
    for entry in show_multiples:
        mname = entry["name"]
        update_lines.append(f'                    "{mname}_media_list": {mname}_media_list,')
    update_lines += [
        "                },",
        "                request=request)",
    ]
    for entry in show_multiples:
        mname = entry["name"]
        mrole = entry["role"]
        update_lines += [
            f'        _{mname}_files_raw = request.files.get("{mname}", [])',
            f'        _{mname}_files = _{mname}_files_raw if isinstance(_{mname}_files_raw, list) else ([_{mname}_files_raw] if _{mname}_files_raw else [])',
            f'        for _{mname}_f in _{mname}_files:',
            f'            if getattr(_{mname}_f, "filename", ""):',
            '                try:',
            f'                    form.fields["{mname}"].validate(_{mname}_f)',
            f'                except Exception as _{mname}_exc:',
            f'                    form.add_error("{mname}", getattr(_{mname}_exc, "messages", [str(_{mname}_exc)]))',
        ]
        for single_entry in show_singles:
            sname = single_entry["name"]
            srole = single_entry["role"]
            update_lines.append(
                f'                    {sname}_media = get_cover_media("{snake}", {pk_name}, role="{srole}")'
            )
        for multi_entry in show_multiples:
            m2name = multi_entry["name"]
            m2role = multi_entry["role"]
            update_lines.append(
                f'                    {m2name}_media_list = list_media_for_entity("{snake}", {pk_name}, role="{m2role}")'
            )
        update_lines += [
            f'                    return BaseController.validation_error("{snake}/form.html",',
            '                        context={',
            '                            "form": form,',
            f'                            "action": f"/{snake}/update/{{{pk_name}}}",',
            f'                            "titre": "Modifier {snake}",',
        ]
        for relation in many_to_many_relations or []:
            update_lines.append(f'                            "{relation.choices_key}": {relation.choices_function}(),')
            update_lines.append(f'                            "{relation.selected_key}": {relation.field_name},')
        for single_entry in show_singles:
            sname = single_entry["name"]
            update_lines.append(f'                            "{sname}_media": {sname}_media,')
        for multi_entry in show_multiples:
            m2name = multi_entry["name"]
            update_lines.append(f'                            "{m2name}_media_list": {m2name}_media_list,')
        update_lines += [
            '                        },',
            '                        request=request)',
        ]
    if ctrl_media_entries:
        media_names_repr = "{" + ", ".join(f'"{e["name"]}"' for e in ctrl_media_entries) + "}"
        update_lines += [
            f'        _media_keys = {media_names_repr}',
            '        _sql_data = {k: v for k, v in form.cleaned_data.items() if k not in _media_keys}',
            f'        update_{snake}({pk_name}, _sql_data)',
        ]
        for entry in ctrl_media_entries:
            if entry.get("multiple", False):
                continue
            mname = entry["name"]
            mrole = entry["role"]
            mfield = entry["field"]
            variants = entry.get("variants", False)
            del_variants = mfield == "image"
            update_lines += [
                f'        _{mname}_alt = (request.body.get("_media_alt_{mname}", [None])[0] or None)',
                f'        _{mname}_file = form.cleaned_data.get("{mname}")',
                f'        _{mname}_has_file = bool(_{mname}_file and getattr(_{mname}_file, "filename", ""))',
                f'        _{mname}_delete = "_delete_media_{mname}" in request.body',
                f'        if _{mname}_has_file or _{mname}_delete:',
                f'            for _old in list_media_for_entity("{snake}", {pk_name}, role="{mrole}"):',
                f'                delete_media(_old["id"], delete_files=True, variants={del_variants})',
                f'            if _{mname}_has_file:',
                f'                _saved_{mname} = {_media_upload_call(mfield, f"_{mname}_file", variants)}',
                f'                attach_media_to_entity(_saved_{mname}, entity_name="{snake}", entity_id={pk_name}, role="{mrole}", position=0, alt_text=_{mname}_alt)',
                '        else:',
                f'            for _existing_{mname} in list_media_for_entity("{snake}", {pk_name}, role="{mrole}"):',
                f'                update_media_alt_text(_existing_{mname}["id"], _{mname}_alt)',
            ]
        for entry in ctrl_media_entries:
            if not entry.get("multiple", False):
                continue
            mname = entry["name"]
            mrole = entry["role"]
            mfield = entry["field"]
            variants = entry.get("variants", False)
            update_lines += [
                f'        _{mname}_del_ids = request.body.get("_delete_media_{mname}", [])',
                f'        for _did in _{mname}_del_ids:',
                '            delete_media(int(_did), delete_files=True, variants=True)',
                '        for _key in list(request.body.keys()):',
                f'            if _key.startswith("_media_position_{mname}_"):',
                '                try:',
                f'                    _pos_mid = int(_key[len("_media_position_{mname}_"):])',
                '                    _pval_raw = request.body.get(_key, [])',
                '                    _pval = int(_pval_raw[0]) if _pval_raw else None',
                '                    if _pval is not None and _pval >= 0:',
                '                        update_media_position(_pos_mid, _pval)',
                '                except (ValueError, IndexError):',
                '                    pass',
                '        for _key in list(request.body.keys()):',
                f'            if _key.startswith("_media_alt_{mname}_"):',
                '                try:',
                f'                    _alt_mid = int(_key[len("_media_alt_{mname}_"):])',
                '                    _alt_raw = request.body.get(_key, [])',
                '                    _alt_val = (_alt_raw[0] or None) if _alt_raw else None',
                '                    update_media_alt_text(_alt_mid, _alt_val)',
                '                except (ValueError, IndexError):',
                '                    pass',
                f'        _{mname}_alt_new = (request.body.get("_media_alt_{mname}_new", [None])[0] or None)',
                f'        for _{mname}_f in _{mname}_files:',
                f'            if getattr(_{mname}_f, "filename", ""):',
                f'                _saved_{mname} = {_media_upload_call(mfield, f"_{mname}_f", variants)}',
                f'                attach_media_to_entity(_saved_{mname}, entity_name="{snake}", entity_id={pk_name}, role="{mrole}", position=0, alt_text=_{mname}_alt_new)',
            ]
    else:
        update_lines.append(f'        update_{snake}({pk_name}, form.cleaned_data)')
    for relation in many_to_many_relations or []:
        update_lines.append(f'        {relation.sync_function}({pk_name}, {relation.field_name})')
    update_lines += [
        '        return BaseController.redirect_with_flash(',
        f'            request, f"/{snake}/show/{{{pk_name}}}", "{entity} mis à jour.")',
    ]
    lines += _with_permission(update_lines, _rbac.get("update"))

    # destroy
    destroy_lines = [
        "",
        "    @staticmethod",
        "    def destroy(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route_params.get("id"))',
        f"        if {pk_name} is None:",
        "            return BaseController.not_found()",
    ]
    if ctrl_media_entries:
        destroy_lines += [
            f'        for _m in list_media_for_entity("{snake}", {pk_name}):',
            '            delete_media(_m["id"], delete_files=True, variants=True)',
        ]
    destroy_lines += [
        f'        delete_{snake}({pk_name})',
        "        if _is_hx_request(request):",
        f"            context = {entity}Controller._list_context(request)",
        f'            return BaseController.render("{snake}/_results.html", context=context, request=request)',
        f'        return BaseController.redirect_with_flash(request, "/{snake}", "{entity} supprimé.")',
        "",
    ]
    lines += _with_permission(destroy_lines, _rbac.get("delete"))

    # bulk_delete — affiche la page de confirmation
    bulk_delete_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def bulk_delete(request: Request) -> Response:",
        f"        ids = {entity}Controller._parse_bulk_ids(request)",
        "        if not ids:",
        f'            return BaseController.redirect_with_flash(request, "/{snake}", "Aucun élément sélectionné.")',
        f'        return BaseController.render("{snake}/bulk_delete_confirm.html",',
        '            context={"ids": ids, "count": len(ids), "flash_html": render_flash_html(request)},',
        "            request=request)",
    ]
    lines += _with_permission(bulk_delete_lines, _rbac.get("delete"))

    # bulk_delete_confirm — effectue la suppression après confirmation
    bulk_delete_confirm_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def bulk_delete_confirm(request: Request) -> Response:",
        f"        ids = {entity}Controller._parse_bulk_ids(request)",
        "        if not ids:",
        f'            return BaseController.redirect_with_flash(request, "/{snake}", "Aucun élément sélectionné.")',
        f"        bulk_delete_{plural}(ids)",
        '        count = len(ids)',
        '        return BaseController.redirect_with_flash(',
        f'            request, "/{snake}",',
        '            f"{count} élément(s) supprimé(s).")',
        "",
    ]
    lines += _with_permission(bulk_delete_confirm_lines, _rbac.get("delete"))

    # _csv_escape — neutralise l'injection CSV
    csv_escape_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def _csv_escape(value: str) -> str:",
        '        if value and value[0] in ("=", "+", "-", "@"):',
        '            return "\'" + value',
        "        return value",
    ]
    lines += csv_escape_lines

    # export_csv — export CSV filtré
    export_csv_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def export_csv(request: Request) -> Response:",
        '        q = _query_param(request, "q").strip()',
        '        sort = _query_param(request, "sort")',
        f"        if sort not in {allowed_sort_keys_repr}:",
        '            sort = ""',
        '        direction = _query_param(request, "direction", "desc")',
        '        if direction not in ("asc", "desc"):',
        '            direction = "asc"',
    ]
    if filter_flds:
        for ff in filter_flds:
            fname = ff["name"]
            if fname in relation_filter_names:
                export_csv_lines += [
                    f'        {fname}_raw = _query_param(request, "{fname}").strip()',
                    f'        {fname}_f = ""',
                    f'        if {fname}_raw:',
                    "            try:",
                    f"                {fname}_f = int({fname}_raw)",
                    "            except (TypeError, ValueError):",
                    f'                {fname}_f = ""',
                ]
            else:
                export_csv_lines.append(f'        {fname}_f = _query_param(request, "{fname}").strip()')
        export_csv_lines.append("        _filters = {}")
        for ff in filter_flds:
            fname = ff["name"]
            if _is_bool_sql(ff.get("sql_type", "")):
                export_csv_lines += [
                    f'        if {fname}_f in ("0", "1"):',
                    f'            _filters["{fname}"] = {fname}_f',
                ]
            else:
                export_csv_lines += [
                    f'        if {fname}_f != "":',
                    f'            _filters["{fname}"] = {fname}_f',
                ]
        export_csv_lines.append(
            f"        rows = find_{plural}_for_export(q=q or None, sort=sort or None, direction=direction, filters=_filters or None)"
        )
    else:
        export_csv_lines.append(
            f"        rows = find_{plural}_for_export(q=q or None, sort=sort or None, direction=direction)"
        )
    export_csv_lines += [
        "        output = io.StringIO()",
        "        writer = csv.writer(output, quoting=csv.QUOTE_ALL)",
        "        writer.writerow([header for header, _ in _CSV_COLS])",
        "        for row in rows:",
        f'            writer.writerow([{entity}Controller._csv_escape(str(row.get(key) or "")) for _, key in _CSV_COLS])',
        '        content = output.getvalue().encode("utf-8")',
        "        return Response(",
        "            200,",
        "            content,",
        '            "text/csv; charset=utf-8",',
        "            headers={",
        f'                "Content-Disposition": \'attachment; filename="{plural}.csv"\',',
        '                "Cache-Control": "no-store",',
        "            },",
        "        )",
        "",
    ]
    lines += _with_permission(export_csv_lines, _rbac.get("index"))

    return "\n".join(lines)
