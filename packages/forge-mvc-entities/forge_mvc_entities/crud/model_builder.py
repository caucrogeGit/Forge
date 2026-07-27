# pyright: strict
# pyright: reportPrivateUsage=false
"""Model builder for the CRUD generator."""

from __future__ import annotations
from typing import Any, cast

from forge_mvc_entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_mvc_entities.crud.utils import (
    _filter_fields,
    _is_generated,
    _is_managed,
    _is_soft_delete,
    _managed_touches_update,
    _non_pk_fields,
    _pk_field,
    _soft_delete_column,
    _text_search_fields,
    _to_snake,
)
from forge_mvc_entities.crud.relations_loader import (
    _build_select_base,
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)
from forge_mvc_entities.field_resolver import dialect


def _column_value_expr(field: dict[str, Any]) -> str:
    """Expression Python de la valeur d'une colonne dans l'INSERT/UPDATE généré.

    Un horodatage géré (ADR-081) est posé par le modèle via
    ``datetime.now(timezone.utc)`` ; les autres colonnes lisent ``data``.
    """
    if _is_managed(field):
        return "datetime.now(timezone.utc)"
    return f'data["{field["name"]}"]'


def _render_model_query(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None,
    non_pk: list[dict[str, Any]],
    pk_name: str,
    pk_col: str,
    table: str,
    plural: str,
) -> list[str]:
    """Recherche, tri, pagination et export du modèle (REFACTOR-BUILDERS-DECOMPOSE-002).

    Extrait de `build_model` à iso-sortie.
    """
    search_fields = _text_search_fields(definition, relations)
    # Pagination : la syntaxe et l'ordre des paramètres appartiennent au
    # dialecte (T-SQL ignore LIMIT et annonce le décalage en premier). Les deux
    # sont lus ensemble, sur le même dialecte, pour qu'ils ne divergent pas.
    active_dialect = dialect()
    page_clause = active_dialect.pagination_clause()
    page_params = ", ".join(active_dialect.pagination_param_order())
    qualifier = f"{table}." if relations else ""
    # Suppression logique (ADR-083) : toute lecture filtre deleted_at IS NULL.
    soft_col = _soft_delete_column(definition)
    initial_clauses = f'["{qualifier}{soft_col} IS NULL"]' if soft_col else "[]"
    search_cols_repr = repr([qualifier + f["column"] for f in search_fields])
    # Les champs gérés (horodatages, deleted_at) ne sont pas triables : absents
    # des vues, ils n'ont pas d'en-tête de tri (ADR-081/083).
    sort_items = [(f["name"], qualifier + f["column"]) for f in non_pk if not _is_managed(f)]
    sort_items.append((pk_name, qualifier + pk_col))
    allowed_sort_repr = "{" + ", ".join(f'"{k}": "{v}"' for k, v in sort_items) + "}"
    filter_flds_model = _filter_fields(definition, relations)
    filter_items = [(f["name"], qualifier + f["column"]) for f in filter_flds_model]
    allowed_filters_repr = "{" + ", ".join(f'"{k}": "{v}"' for k, v in filter_items) + "}"

    lines: list[str] = [
        "",
        f"_SEARCH_COLS  = {search_cols_repr}",
        f"_ALLOWED_SORT = {allowed_sort_repr}",
        f"_ALLOWED_FILTERS = {allowed_filters_repr}",
        f'_DEFAULT_SORT = "{qualifier}{pk_col}"',
        "",
        "",
        f"def count_{plural}(q: str | None = None, filters: dict[str, Any] | None = None) -> int:",
        f"    clauses: list[str] = {initial_clauses}",
        "    params: list[Any] = []",
        "    if q and _SEARCH_COLS:",
        '        clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")',
        '        params.extend("%" + q + "%" for _ in _SEARCH_COLS)',
        "    for key, val in (filters or {}).items():",
        '        if val is not None and val != "":',
        "            col = _ALLOWED_FILTERS.get(key)",
        "            if col is None:",
        '                raise ValueError(f"Filtre interdit : {key}")',
        '            clauses.append(col + " = ?")',
        "            params.append(val)",
        "    if clauses:",
        f'        sql = "SELECT COUNT(*) AS total FROM {table} WHERE " + " AND ".join(clauses)',
        "    else:",
        f'        sql = "SELECT COUNT(*) AS total FROM {table}"',
        "    row = fetch_one(sql, params)",
        '    return row["total"] if row else 0',
        "",
        "",
        f'def find_{plural}_paginated(q: str | None = None, sort: str | None = None, direction: str = "asc", limit: int = 10, offset: int = 0, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:',
        "    sort_col = _ALLOWED_SORT.get(sort or \"\", _DEFAULT_SORT)",
        '    sort_dir = "DESC" if direction == "desc" else "ASC"',
        f'    base = "{_build_select_base(table, relations)}"',
        f"    clauses: list[str] = {initial_clauses}",
        "    params: list[Any] = []",
        "    if q and _SEARCH_COLS:",
        '        clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")',
        '        params.extend("%" + q + "%" for _ in _SEARCH_COLS)',
        "    for key, val in (filters or {}).items():",
        '        if val is not None and val != "":',
        "            col = _ALLOWED_FILTERS.get(key)",
        "            if col is None:",
        '                raise ValueError(f"Filtre interdit : {key}")',
        '            clauses.append(col + " = ?")',
        "            params.append(val)",
        "    if clauses:",
        f'        sql = base + " WHERE " + " AND ".join(clauses) + " ORDER BY " + sort_col + " " + sort_dir + "{page_clause}"',
        "    else:",
        f'        sql = base + " ORDER BY " + sort_col + " " + sort_dir + "{page_clause}"',
        f"    params.extend([{page_params}])",
        "    return fetch_all(sql, params)",
        "",
    ]
    lines.extend([
        "",
        "",
        "_EXPORT_LIMIT = 1000",
        "",
        "",
        f'def find_{plural}_for_export(q: str | None = None, sort: str | None = None, direction: str = "asc", filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:',
        f"    return find_{plural}_paginated(",
        "        q=q, sort=sort, direction=direction,",
        "        limit=_EXPORT_LIMIT, offset=0, filters=filters,",
        "    )",
        "",
    ])
    return lines


def _render_model_relations(
    relations: list[CrudManyToOneRelation] | None,
    many_to_many_relations: list[CrudManyToManyRelation] | None,
    pk_name: str,
) -> list[str]:
    """Fonctions de choix (many-to-one) et de pivot (many-to-many) du modèle
    (REFACTOR-BUILDERS-DECOMPOSE-002). Extrait de `build_model` à iso-sortie.
    """
    lines: list[str] = []
    for relation in _unique_choice_relations(relations):
        select_cols = (
            relation.target_pk_column
            if relation.target_label_column == relation.target_pk_column else
            f"{relation.target_pk_column}, {relation.target_label_column}"
        )
        lines.extend([
            "",
            "",
            f"def {relation.choices_function}():",
            f'    rows = fetch_all("SELECT {select_cols} FROM {relation.target_table} ORDER BY {relation.target_label_column}")',
            f'    return [(row["{relation.target_pk_column}"], row["{relation.target_label_column}"]) for row in rows]',
        ])
    for relation in _unique_many_to_many_choice_relations(many_to_many_relations):
        select_cols = (
            relation.target_pk_column
            if relation.target_label_column == relation.target_pk_column else
            f"{relation.target_pk_column}, {relation.target_label_column}"
        )
        lines.extend([
            "",
            "",
            f"def {relation.choices_function}():",
            f'    rows = fetch_all("SELECT {select_cols} FROM {relation.target_table} ORDER BY {relation.target_label_column}")',
            f'    return [(row["{relation.target_pk_column}"], row["{relation.target_label_column}"]) for row in rows]',
        ])
    for relation in many_to_many_relations or []:
        lines.extend([
            "",
            "",
            f"def {relation.selected_function}({pk_name}):",
            f'    rows = fetch_all("SELECT {relation.target_key} FROM {relation.pivot_table} WHERE {relation.source_key} = ?", ({pk_name},))',
            f'    return [row["{relation.target_key}"] for row in rows]',
            "",
            "",
            f"def {relation.list_labels_function}({pk_name}s):",
            f"    if not {pk_name}s:",
            "        return {}",
            f"    placeholders = \", \".join(\"?\" for _ in {pk_name}s)",
            "    rows = fetch_all(",
            f'        "SELECT pivot.{relation.source_key} AS source_id, {relation.target_table}.{relation.target_pk_column} AS target_id, {relation.target_table}.{relation.target_label_column} AS target_label "',
            f'        "FROM {relation.pivot_table} pivot "',
            f'        "JOIN {relation.target_table} ON {relation.target_table}.{relation.target_pk_column} = pivot.{relation.target_key} "',
            f'        "WHERE pivot.{relation.source_key} IN (" + placeholders + ") "',
            f'        "ORDER BY {"pivot." + relation.order_column if relation.order_column else relation.target_table + "." + relation.target_label_column}",',
            f"        tuple({pk_name}s),",
            "    )",
            "    grouped = {}",
            "    for row in rows:",
            '        grouped.setdefault(row["source_id"], []).append(row["target_label"])',
            "    return grouped",
            "",
            "",
            f"def {relation.show_labels_function}({pk_name}):",
            "    rows = fetch_all(",
            f'        "SELECT {relation.target_table}.{relation.target_pk_column} AS target_id, {relation.target_table}.{relation.target_label_column} AS target_label "',
            f'        "FROM {relation.pivot_table} pivot "',
            f'        "JOIN {relation.target_table} ON {relation.target_table}.{relation.target_pk_column} = pivot.{relation.target_key} "',
            f'        "WHERE pivot.{relation.source_key} = ? "',
            f'        "ORDER BY {"pivot." + relation.order_column if relation.order_column else relation.target_table + "." + relation.target_label_column}",',
            f"        ({pk_name},),",
            "    )",
            '    return [row["target_label"] for row in rows]',
            "",
            "",
            f"def {relation.add_function}({pk_name}, selected_ids):",
            "    from core.database.transaction import transaction",
            "    with transaction() as tx:",
            "        for target_id in selected_ids:",
            f'            execute("INSERT INTO {relation.pivot_table} ({relation.source_key}, {relation.target_key}) VALUES (?, ?)", ({pk_name}, target_id), tx=tx)',
            "",
            "",
            f"def {relation.sync_function}({pk_name}, selected_ids):",
            "    from core.database.transaction import transaction",
            "    with transaction() as tx:",
            f'        execute("DELETE FROM {relation.pivot_table} WHERE {relation.source_key} = ?", ({pk_name},), tx=tx)',
            "        for target_id in selected_ids:",
            f'            execute("INSERT INTO {relation.pivot_table} ({relation.source_key}, {relation.target_key}) VALUES (?, ?)", ({pk_name}, target_id), tx=tx)',
        ])
    return lines


def build_model(
    definition: dict[str, Any],
    relations: list[CrudManyToOneRelation] | None = None,
    many_to_many_relations: list[CrudManyToManyRelation] | None = None,
) -> str:
    entity = definition["entity"]
    snake = _to_snake(entity)
    plural = snake + "s"
    table = definition["table"]
    pk = _pk_field(definition)
    pk_col = pk["column"]
    pk_name = pk["name"]
    non_pk = _non_pk_fields(definition)
    auto_inc = pk.get("auto_increment", False)
    # Champs slug → lookup get_<snake>_by_<slug>() pour le routing public (ADR-017).
    slug_fields = [f for f in definition["fields"] if cast("dict[str, Any]", f.get("form") or {}).get("field") == "slug"]

    # Suppression logique (ADR-083) : deleted_at n'est jamais posé à la création
    # ni à l'édition (exclu de l'INSERT), le modèle le pose à la suppression, et
    # toute lecture filtre deleted_at IS NULL.
    soft_col = _soft_delete_column(definition)
    main_q = (table + ".") if relations else ""
    soft_where_all = f" WHERE {main_q}{soft_col} IS NULL" if soft_col else ""
    soft_where_by_id = f" AND {main_q}{soft_col} IS NULL" if soft_col else ""

    insert_fields = [f for f in (non_pk if auto_inc else definition["fields"]) if not _is_soft_delete(f)]
    insert_cols = ", ".join(f["column"] for f in insert_fields)
    insert_placeholders = ", ".join("?" for _ in insert_fields)
    insert_values = ", ".join(_column_value_expr(f) for f in insert_fields)

    if insert_fields and auto_inc:
        new_insert_exec = f"return insert(INSERT, ({insert_values},))"
    elif insert_fields:
        new_insert_exec = f"execute(INSERT, ({insert_values},))"
    else:
        new_insert_exec = "execute(INSERT)"

    # Champs exclus de l'UPDATE car stables à l'édition : un champ auto-généré
    # (slug avec source, ADR-017 D4) et un horodatage de création (created_at,
    # ADR-081). L'horodatage de mise à jour (updated_at) reste dans l'UPDATE,
    # réécrit à chaque fois par le modèle.
    update_fields = [
        f for f in non_pk
        if not _is_generated(f)
        and not (_is_managed(f) and not _managed_touches_update(f))
    ]
    if update_fields:
        update_set = ", ".join(f'{f["column"]} = ?' for f in update_fields)
        update_values = ", ".join(_column_value_expr(f) for f in update_fields)
        update_constant = f'"UPDATE {table} SET {update_set} WHERE {pk_col} = ?"'
        update_exec = f"execute(UPDATE, ({update_values}, {pk_name}))"
    else:
        update_constant = "None  # aucun champ métier — UPDATE non applicable"
        update_exec = "return  # aucun champ à mettre à jour"

    # Import datetime si le modèle pose une valeur temporelle : horodatage géré
    # (ADR-081) ou marque de suppression logique (ADR-083). Sinon l'import serait
    # inutilisé (ruff F401).
    needs_datetime = (
        any(_is_managed(f) for f in insert_fields)
        or any(_is_managed(f) for f in update_fields)
        or bool(soft_col)
    )

    # Suppression : logique (UPDATE deleted_at = now) si soft_delete, sinon
    # physique (DELETE). Idem pour la suppression groupée.
    if soft_col:
        delete_constant = f'"UPDATE {table} SET {soft_col} = ? WHERE {pk_col} = ?"'
        delete_exec = f"execute(DELETE, (datetime.now(timezone.utc), {pk_name}))"
        bulk_delete_sql = f'"UPDATE {table} SET {soft_col} = ? WHERE {pk_col} IN (" + placeholders + ")"'
        bulk_delete_params = "[datetime.now(timezone.utc), *ids]"
    else:
        delete_constant = f'"DELETE FROM {table} WHERE {pk_col} = ?"'
        delete_exec = f"execute(DELETE, ({pk_name},))"
        bulk_delete_sql = f'"DELETE FROM {table} WHERE {pk_col} IN (" + placeholders + ")"'
        bulk_delete_params = "list(ids)"

    lines: list[str] = [
        *(["from datetime import datetime, timezone", ""] if needs_datetime else []),
        "from typing import Any",
        "",
        "from core.database.db import fetch_one, fetch_all, execute, insert",
        "",
        f'SELECT_ALL   = "{_build_select_base(table, relations)}{soft_where_all} ORDER BY {main_q}{pk_col}"',
        f'SELECT_BY_ID = "{_build_select_base(table, relations)} WHERE {main_q}{pk_col} = ?{soft_where_by_id}"',
        f'INSERT       = "INSERT INTO {table} ({insert_cols}) VALUES ({insert_placeholders})"',
        f'UPDATE       = {update_constant}',
        f'DELETE       = {delete_constant}',
        "",
        "",
        f"def get_{plural}():",
        "    return fetch_all(SELECT_ALL)",
        "",
        "",
        f"def get_{snake}_by_id({pk_name}):",
        f"    return fetch_one(SELECT_BY_ID, ({pk_name},))",
        "",
        "",
        f"def add_{snake}(data):",
        f"    {new_insert_exec}",
        "",
        "",
        f"def update_{snake}({pk_name}, data):",
        f"    {update_exec}",
        "",
        "",
        f"def delete_{snake}({pk_name}):",
        f"    {delete_exec}",
        "",
        "",
        f"def bulk_delete_{plural}(ids):",
        '    """Supprime plusieurs enregistrements par ID. Aucune concaténation SQL."""',
        "    if not ids:",
        "        return",
        '    placeholders = ", ".join("?" for _ in ids)',
        f"    execute({bulk_delete_sql}, {bulk_delete_params})",
        "",
    ]

    lines += _render_model_query(definition, relations, non_pk, pk_name, pk_col, table, plural)
    lines += _render_model_relations(relations, many_to_many_relations, pk_name)

    # Lookup par slug : inséré juste après get_<snake>_by_id (routing public).
    if slug_fields:
        anchor = f"    return fetch_one(SELECT_BY_ID, ({pk_name},))"
        pos = lines.index(anchor) + 1
        block: list[str] = []
        for sf in slug_fields:
            sname = sf["name"]
            scol = sf["column"]
            block += [
                "",
                "",
                f"def get_{snake}_by_{sname}({sname}):",
                f'    return fetch_one("SELECT * FROM {table} WHERE {scol} = ?{" AND " + soft_col + " IS NULL" if soft_col else ""}", ({sname},))',
            ]
        lines[pos:pos] = block

    return "\n".join(lines)
