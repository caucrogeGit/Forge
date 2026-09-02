# pyright: strict
# pyright: reportPrivateUsage=false
"""Controller builder for the CRUD generator."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, cast

from forge_mvc_entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_mvc_entities.crud.utils import (
    _filter_fields,
    _humanize,
    _is_bool_sql,
    _is_generated,
    _is_managed,
    _media_form_fields,
    _non_pk_fields,
    _pk_field,
    _relation_by_field,
    _to_snake,
)
from forge_mvc_entities.crud.context import _with_permission


def _media_upload_call(mfield: str, var: str, variants: object) -> str:
    """Expression d'upload générée pour un champ média.

    CORE-SAVEUPLOAD-GENERIC-CLEANUP (ADR-018) : les champs **image** passent par
    le chemin image-aware de l'opt-in (`save_image_upload`, vérification de
    contenu + variantes) ; les autres fichiers utilisent le `save_upload`
    **générique** du core.

    IMAGES-ENTITY-FIELD-001 : `variants` peut être une liste de noms de
    préréglages. Elle est rendue en littéral Python, `repr` donnant la même
    forme pour un booléen et pour une liste de chaînes.
    """
    if mfield == "image":
        return f'save_image_upload({var}, "images", variants={variants!r})'
    return f'save_upload({var}, "documents")'
from forge_mvc_entities.crud.relations_loader import (
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)
from forge_mvc_entities.crud.views_namespace import entity_view_dir


@dataclass(frozen=True)
class _ControllerContext:
    """Locaux partagés du générateur (REFACTOR-BUILD-CONTROLLER-001).

    Calculés une fois par `build_controller`, passés aux sous-générateurs
    `_render_*(ctx)` qui produisent chacun les lignes d'une partie du contrôleur.
    """
    entity: str
    snake: str
    view_dir: str  # dossier de vues relatif à mvc/views/ (ADR-073), ex. "app/eleve"
    plural: str
    pk_name: str
    choice_options: list[CrudManyToOneRelation]
    generated_fields: list[tuple[str, str]]
    ctrl_media_entries: list[dict[str, Any]]
    m2m: list[CrudManyToManyRelation]
    allowed_sort_keys_repr: str
    filter_flds: list[dict[str, Any]]
    relation_filter_names: set[str]
    # Champs porteurs d'une contrainte UNIQUE (CRUD-DUP-HANDLING-001). Vide =
    # aucun garde anti-doublon n'est émis, la sortie reste celle d'avant.
    unique_fields: list[str]


def _render_export_csv(ctx: _ControllerContext) -> list[str]:
    # `entity` n'est plus nécessaire ici : l'échappement CSV ne passe plus par
    # une méthode de la classe générée mais par `core.security.csv_export`
    # (ticket CRUD-CSV-ESCAPE-CORE-001).
    plural = ctx.plural
    allowed_sort_keys_repr = ctx.allowed_sort_keys_repr
    filter_flds = ctx.filter_flds
    relation_filter_names = ctx.relation_filter_names
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
        '            writer.writerow([escape_csv_field(str(row.get(key) or "")) for _, key in _CSV_COLS])',
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
    return export_csv_lines


def _render_new(ctx: _ControllerContext) -> list[str]:
    entity, snake, choice_options, many_to_many_relations = ctx.entity, ctx.snake, ctx.choice_options, ctx.m2m
    new_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def new(request: Request) -> Response:",
        (
            f'        form = {entity}Form(**_{snake}_form_options())'
            if choice_options else
            f'        form = {entity}Form()'
        ),
        f'        return BaseController.render("{ctx.view_dir}/form.html",',
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
    return new_lines


def _render_destroy(ctx: _ControllerContext) -> list[str]:
    entity, snake, pk_name, ctrl_media_entries = ctx.entity, ctx.snake, ctx.pk_name, ctx.ctrl_media_entries
    destroy_lines = [
        "",
        "    @staticmethod",
        "    def destroy(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route("id"))',
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
        f'            return BaseController.render("{ctx.view_dir}/_results.html", context=context, request=request)',
        f'        return BaseController.redirect_with_flash(request, "/{snake}", "{entity} supprimé.")',
        "",
    ]
    return destroy_lines


def _render_bulk_delete(ctx: _ControllerContext) -> list[str]:
    entity, snake = ctx.entity, ctx.snake
    bulk_delete_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def bulk_delete(request: Request) -> Response:",
        f"        ids = {entity}Controller._parse_bulk_ids(request)",
        "        if not ids:",
        f'            return BaseController.redirect_with_flash(request, "/{snake}", "Aucun élément sélectionné.")',
        f'        return BaseController.render("{ctx.view_dir}/bulk_delete_confirm.html",',
        '            context={"ids": ids, "count": len(ids), "flash": get_flash(get_session_id(request))},',
        "            request=request)",
    ]
    return bulk_delete_lines


def _render_bulk_delete_confirm(ctx: _ControllerContext) -> list[str]:
    entity, snake, plural = ctx.entity, ctx.snake, ctx.plural
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
    return bulk_delete_confirm_lines


def _render_csv_escape(_ctx: _ControllerContext) -> list[str]:
    """Plus rien à rendre : la neutralisation vient du cœur.

    Le contrôleur généré portait sa propre copie de la règle anti-injection de
    formule CSV. Recopiée dans chaque contrôleur, elle devenait incorrigible :
    Forge ne réécrit jamais le code utilisateur (principe 9), donc une règle
    incomplète le restait dans tous les fichiers déjà générés. Elle vit
    désormais dans `core.security.csv_export.escape_csv_field`, que le
    contrôleur **appelle**.

    La fonction est conservée, vide, pour garder la trace de ce choix à
    l'endroit où la duplication se produisait (ticket
    `CRUD-CSV-ESCAPE-CORE-001`).
    """
    return []


def _duplicate_error_line(ctx: _ControllerContext, indent: str) -> str:
    """Ligne qui rattache l'erreur de doublon (CRUD-DUP-HANDLING-001).

    Avec un seul champ unique, l'erreur se pose dessus et s'affiche sous lui.
    Avec plusieurs, l'exception ne dit pas laquelle des contraintes a sauté (le
    nom n'est pas normalisé entre SGBD) : on pose alors une erreur globale
    plutôt que d'en désigner une au hasard.
    """
    if len(ctx.unique_fields) == 1:
        return (
            f'{indent}form.add_error("{ctx.unique_fields[0]}", '
            '"Cette valeur est déjà utilisée.")'
        )
    return (
        f'{indent}form.add_error(None, "Une valeur saisie est déjà utilisée '
        'pour un champ qui doit être unique.")'
    )


def _rerender_form_lines(ctx: _ControllerContext, indent: str, items: list[str]) -> list[str]:
    """Bloc `validation_error` qui réaffiche le formulaire, à l'indentation donnée.

    Partagé par la branche « formulaire invalide » et la branche « doublon »,
    pour que les deux réaffichent strictement le même écran.
    """
    lines = [
        f'{indent}return BaseController.validation_error("{ctx.view_dir}/form.html",',
        f'{indent}    context={{',
    ]
    lines += [f'{indent}        {item}' for item in items]
    lines += [
        f'{indent}    }},',
        f'{indent}    request=request)',
    ]
    return lines


def _guard_duplicate(ctx: _ControllerContext, persist_lines: list[str],
                     items: list[str], base_indent: str,
                     pre_lines: list[str] | None = None) -> list[str]:
    """Entoure les lignes de persistance d'un garde anti-doublon.

    Sans champ unique, les lignes sont rendues telles quelles : la sortie du
    générateur reste identique à ce qu'elle était pour ces entités.

    `pre_lines` sert au réaffichage de `update`, qui doit relire les médias en
    base avant de rendre le formulaire (l'entité existe déjà).
    """
    if not ctx.unique_fields:
        return persist_lines
    guarded = [f'{base_indent}try:']
    guarded += [f'    {line}' for line in persist_lines]
    guarded.append(f'{base_indent}except UniqueViolationError:')
    guarded.append(_duplicate_error_line(ctx, base_indent + "    "))
    guarded += pre_lines or []
    guarded += _rerender_form_lines(ctx, base_indent + "    ", items)
    return guarded


def _render_create(ctx: _ControllerContext) -> list[str]:
    entity, snake, choice_options, generated_fields, ctrl_media_entries, many_to_many_relations = ctx.entity, ctx.snake, ctx.choice_options, ctx.generated_fields, ctx.ctrl_media_entries, ctx.m2m
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
    # Contexte de réaffichage du formulaire, partagé par toutes les branches
    # qui le rendent à nouveau (invalide, fichier refusé, doublon).
    rerender_items = [
        '"form": form,',
        f'"action": "/{snake}/create",',
        f'"titre": "Nouveau {snake}",',
    ]
    for relation in many_to_many_relations or []:
        rerender_items.append(f'"{relation.choices_key}": {relation.choices_function}(),')
        rerender_items.append(f'"{relation.selected_key}": {relation.field_name},')
    create_lines.append("        if not form.is_valid():")
    create_lines += _rerender_form_lines(ctx, "            ", rerender_items)
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
                f'        _{mname}_files = request.files_list("{mname}")',
                f'        for _{mname}_f in _{mname}_files:',
                f'            if getattr(_{mname}_f, "filename", ""):',
                '                try:',
                f'                    form.fields["{mname}"].validate(_{mname}_f)',
                f'                except Exception as _{mname}_exc:',
                f'                    form.add_error("{mname}", getattr(_{mname}_exc, "messages", [str(_{mname}_exc)]))',
            ]
            create_lines += _rerender_form_lines(ctx, "                    ", rerender_items)
        media_names_repr = "{" + ", ".join(f'"{e["name"]}"' for e in ctrl_media_entries) + "}"
        create_lines += [
            f'        _media_keys = {media_names_repr}',
            '        _sql_data = {k: v for k, v in form.cleaned_data.items() if k not in _media_keys}',
        ]
        create_lines += _guard_duplicate(
            ctx, [f'        created_id = add_{snake}(_sql_data)'], rerender_items, "        "
        )
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
            persist = [f'        created_id = add_{snake}(form.cleaned_data)']
        else:
            persist = [f'        add_{snake}(form.cleaned_data)']
        create_lines += _guard_duplicate(ctx, persist, rerender_items, "        ")
    for relation in many_to_many_relations or []:
        create_lines.append(f'        {relation.add_function}(created_id, {relation.field_name})')
    create_lines.append(
        f'        return BaseController.redirect_with_flash(request, "/{snake}", "{entity} créé.")'
    )
    return create_lines


def _render_show(ctx: _ControllerContext) -> list[str]:
    snake, entity, pk_name, ctrl_media_entries, many_to_many_relations = ctx.snake, ctx.entity, ctx.pk_name, ctx.ctrl_media_entries, ctx.m2m
    show_singles = [e for e in ctrl_media_entries if not e.get("multiple", False)]
    show_multiples = [e for e in ctrl_media_entries if e.get("multiple", False)]
    show_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def show(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route("id"))',
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
    ctx_items = [f'"{snake}": {snake}', '"flash": get_flash(get_session_id(request))']
    ctx_items += [f'"{relation.show_context_key}": {relation.show_context_key}' for relation in many_to_many_relations or []]
    ctx_items += [f'"{e["name"]}_media": {e["name"]}_media' for e in show_singles]
    ctx_items += [f'"{e["name"]}_media_list": {e["name"]}_media_list' for e in show_multiples]
    show_lines += [
        f'        return BaseController.render("{ctx.view_dir}/show.html",',
        f'            context={{{", ".join(ctx_items)}}},',
        "            request=request)",
    ]
    return show_lines


def _render_edit(ctx: _ControllerContext) -> list[str]:
    snake, entity, pk_name, choice_options, ctrl_media_entries, many_to_many_relations = ctx.snake, ctx.entity, ctx.pk_name, ctx.choice_options, ctx.ctrl_media_entries, ctx.m2m
    show_singles = [e for e in ctrl_media_entries if not e.get("multiple", False)]
    show_multiples = [e for e in ctrl_media_entries if e.get("multiple", False)]
    edit_singles = show_singles  # same list
    edit_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def edit(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route("id"))',
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
        f'        return BaseController.render("{ctx.view_dir}/form.html",',
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
    return edit_lines


def _render_update(ctx: _ControllerContext) -> list[str]:
    entity, snake, pk_name, choice_options, ctrl_media_entries, many_to_many_relations = ctx.entity, ctx.snake, ctx.pk_name, ctx.choice_options, ctx.ctrl_media_entries, ctx.m2m
    show_singles = [e for e in ctrl_media_entries if not e.get("multiple", False)]
    show_multiples = [e for e in ctrl_media_entries if e.get("multiple", False)]
    update_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def update(request: Request) -> Response:",
        f'        {pk_name} = {entity}Controller._parse_id(request.route("id"))',
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
    # Contexte de réaffichage, partagé par les branches invalide / fichier
    # refusé / doublon. Les médias sont relus en base : l'entité existe déjà.
    rerender_items = [
        '"form": form,',
        f'"action": f"/{snake}/update/{{{pk_name}}}",',
        f'"titre": "Modifier {snake}",',
    ]
    for relation in many_to_many_relations or []:
        rerender_items.append(f'"{relation.choices_key}": {relation.choices_function}(),')
        rerender_items.append(f'"{relation.selected_key}": {relation.field_name},')
    for entry in show_singles:
        rerender_items.append(f'"{entry["name"]}_media": {entry["name"]}_media,')
    for entry in show_multiples:
        rerender_items.append(f'"{entry["name"]}_media_list": {entry["name"]}_media_list,')

    def _media_reload(indent: str) -> list[str]:
        """Relecture des médias avant un réaffichage du formulaire."""
        out: list[str] = []
        for e in show_singles:
            out.append(
                f'{indent}{e["name"]}_media = get_cover_media("{snake}", {pk_name}, role="{e["role"]}")'
            )
        for e in show_multiples:
            out.append(
                f'{indent}{e["name"]}_media_list = list_media_for_entity("{snake}", {pk_name}, role="{e["role"]}")'
            )
        return out

    update_lines += _rerender_form_lines(ctx, "            ", rerender_items)
    for entry in show_multiples:
        mname = entry["name"]
        mrole = entry["role"]
        update_lines += [
            f'        _{mname}_files = request.files_list("{mname}")',
            f'        for _{mname}_f in _{mname}_files:',
            f'            if getattr(_{mname}_f, "filename", ""):',
            '                try:',
            f'                    form.fields["{mname}"].validate(_{mname}_f)',
            f'                except Exception as _{mname}_exc:',
            f'                    form.add_error("{mname}", getattr(_{mname}_exc, "messages", [str(_{mname}_exc)]))',
        ]
        update_lines += _media_reload("                    ")
        update_lines += _rerender_form_lines(ctx, "                    ", rerender_items)
    if ctrl_media_entries:
        media_names_repr = "{" + ", ".join(f'"{e["name"]}"' for e in ctrl_media_entries) + "}"
        update_lines += [
            f'        _media_keys = {media_names_repr}',
            '        _sql_data = {k: v for k, v in form.cleaned_data.items() if k not in _media_keys}',
        ]
        update_lines += _guard_duplicate(
            ctx, [f'        update_{snake}({pk_name}, _sql_data)'],
            rerender_items, "        ", pre_lines=_media_reload("            "),
        )
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
        update_lines += _guard_duplicate(
            ctx, [f'        update_{snake}({pk_name}, form.cleaned_data)'],
            rerender_items, "        ", pre_lines=_media_reload("            "),
        )
    for relation in many_to_many_relations or []:
        update_lines.append(f'        {relation.sync_function}({pk_name}, {relation.field_name})')
    update_lines += [
        '        return BaseController.redirect_with_flash(',
        f'            request, f"/{snake}/show/{{{pk_name}}}", "{entity} mis à jour.")',
    ]
    return update_lines


def _render_index(ctx: _ControllerContext) -> list[str]:
    entity = ctx.entity
    index_lines: list[str] = [
        "",
        "    @staticmethod",
        "    def index(request: Request) -> Response:",
        f"        context = {entity}Controller._list_context(request)",
        f'        template = "{ctx.view_dir}/_results.html" if _is_hx_request(request) else "{ctx.view_dir}/index.html"',
        "        return BaseController.render(template, context=context, request=request)",
    ]
    return index_lines


def _render_list_context(ctx: _ControllerContext, pk_col: str) -> list[str]:
    """Méthode `_list_context` du contrôleur (REFACTOR-BUILDERS-DECOMPOSE-002).

    Lecture des paramètres de liste, filtres, pagination et contexte de rendu.
    Extraite de `build_controller` à iso-sortie.
    """
    allowed_sort_keys_repr = ctx.allowed_sort_keys_repr
    filter_flds = ctx.filter_flds
    relation_filter_names = ctx.relation_filter_names
    plural = ctx.plural
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
        for relation in ctx.choice_options:
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
        "                \"flash\": get_flash(get_session_id(request)),",
    ])
    for relation in ctx.m2m:
        list_context_lines.append(
            f'                "{relation.list_context_key}": {relation.list_labels_function}([row["{pk_col}"] for row in {plural}]),'
        )
    list_context_lines.extend([
        "            }",
    ])
    return list_context_lines


def _render_preamble(
    entity: str,
    snake: str,
    plural: str,
    non_pk: list[dict[str, Any]],
    generated_fields: list[tuple[str, str]],
    choice_imports: list[str],
    many_to_many_imports: list[str],
    ctrl_media_entries: list[dict[str, Any]],
    choice_options: list[CrudManyToOneRelation],
    relations: list[CrudManyToOneRelation] | None,
    has_rbac: bool,
    unique_fields: list[str],
) -> list[str]:
    """Préambule du module contrôleur (REFACTOR-BUILDERS-DECOMPOSE-002).

    Imports, helpers de module (`_form_data_from_*`, `_query_param`,
    `_is_hx_request`) et constante `_CSV_COLS`, jusqu'avant la classe.
    Extrait de `build_controller` à iso-sortie.
    """
    lines: list[str] = [
        "import csv",
        "import io",
        "from core.security.csv_export import escape_csv_field",
        "from core.http.request import Request",
        "from core.http.response import Response",
    ]
    if generated_fields:
        lines.append("from core.http.slug import slugify")
    if unique_fields:
        # Doublon sur un champ UNIQUE : erreur de formulaire, pas une 500
        # (CRUD-DUP-HANDLING-001). L'exception est portable entre backends.
        lines.append("from core.database.errors import UniqueViolationError")
    if has_rbac:
        lines.append("from forge_mvc_rbac import require_permission")
    lines += [
        "from core.mvc.controller import BaseController",
        "from core.mvc.view.pagination import Pagination",
        f"from mvc.models.{snake}_model import (",
        f"    get_{snake}_by_id, add_{snake}, update_{snake}, delete_{snake}, bulk_delete_{plural},",
        f"    count_{plural}, find_{plural}_paginated, find_{plural}_for_export,",
    ]
    if choice_imports:
        lines.append(f"    {', '.join(choice_imports)},")
    if many_to_many_imports:
        lines.append(f"    {', '.join(many_to_many_imports)},")
    lines.extend([
        ")",
        f"from mvc.forms.{snake}_form import {entity}Form",
        "from core.security.session import get_flash, get_session_id",
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
    _csv_cols: list[tuple[str, str]] = []
    for _f in non_pk:
        _fname = _f["name"]
        _rel = _rel_by_field.get(_fname)
        _header = _humanize(_fname)
        _row_key = f"{_fname}_label" if _rel else _f["column"]
        _csv_cols.append((_header, _row_key))
    lines.append(f"_CSV_COLS = {_csv_cols!r}")
    lines.append("")
    lines.append("")
    return lines


def build_controller(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
    views_namespace: str = "",
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    view_dir = entity_view_dir(snake, views_namespace)
    plural = snake + "s"
    pk = _pk_field(definition)
    pk_name = pk["name"]
    pk_col = pk["column"]
    # Les horodatages gérés (ADR-081) ne sont surfacés dans aucun artefact
    # utilisateur : ni tri, ni export CSV, ni préremplissage de formulaire.
    # Leur valeur est posée par le modèle et reste consultable en base.
    non_pk = [f for f in _non_pk_fields(definition) if not _is_managed(f)]
    # Champs slug auto-générés : (nom, champ source) — calculés à la création.
    generated_fields = [(f["name"], f["source"]) for f in non_pk if _is_generated(f)]
    # Champs UNIQUE : la contrainte existe déjà en base, mais l'INSERT n'était
    # gardé pour aucun d'eux (CRUD-DUP-HANDLING-001), d'où une 500 sur doublon.
    unique_fields = [f["name"] for f in non_pk if f.get("unique") is True]
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
    _rbac_raw: dict[str, Any] = cast("dict[str, Any]", definition.get("rbac") or {}).get("permissions") or {}
    _rbac: dict[str, str] = {}
    if _rbac_raw:
        from forge_mvc_rbac import normalize_permission_code
        _rbac = {
            action: normalize_permission_code(code)
            for action, code in _rbac_raw.items()
            if isinstance(code, str) and code.strip()
        }

    lines: list[str] = _render_preamble(
        entity, snake, plural, non_pk, generated_fields, choice_imports,
        many_to_many_imports, ctrl_media_entries, choice_options, relations, bool(_rbac),
        unique_fields,
    )
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
    _ctx = _ControllerContext(
        entity=entity, snake=snake, view_dir=view_dir, plural=plural, pk_name=pk_name,
        choice_options=choice_options, generated_fields=generated_fields,
        ctrl_media_entries=ctrl_media_entries, m2m=many_to_many_relations or [],
        allowed_sort_keys_repr=allowed_sort_keys_repr,
        filter_flds=filter_flds, relation_filter_names=relation_filter_names,
        unique_fields=unique_fields,
    )
    lines += _render_list_context(_ctx, pk_col)

    lines += _with_permission(_render_index(_ctx), _rbac.get("index"))

    lines += _with_permission(_render_new(_ctx), _rbac.get("create"))

    lines += _with_permission(_render_create(_ctx), _rbac.get("store"))

    lines += _with_permission(_render_show(_ctx), _rbac.get("show"))

    lines += _with_permission(_render_edit(_ctx), _rbac.get("edit"))

    lines += _with_permission(_render_update(_ctx), _rbac.get("update"))

    lines += _with_permission(_render_destroy(_ctx), _rbac.get("delete"))

    lines += _with_permission(_render_bulk_delete(_ctx), _rbac.get("delete"))

    lines += _with_permission(_render_bulk_delete_confirm(_ctx), _rbac.get("delete"))

    lines += _render_csv_escape(_ctx)

    lines += _with_permission(_render_export_csv(_ctx), _rbac.get("index"))

    return "\n".join(lines)
