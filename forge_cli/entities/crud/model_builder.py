"""Model builder for the CRUD generator."""

from __future__ import annotations

from forge_cli.entities.crud.context import (
    CrudManyToOneRelation,
    CrudManyToManyRelation,
)
from forge_cli.entities.crud.utils import (
    _filter_fields,
    _is_generated,
    _non_pk_fields,
    _pk_field,
    _text_search_fields,
    _to_snake,
)
from forge_cli.entities.crud.relations_loader import (
    _build_select_base,
    _unique_choice_relations,
    _unique_many_to_many_choice_relations,
)


def build_model(
    definition: dict,
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

    insert_fields = non_pk if auto_inc else definition["fields"]
    insert_cols = ", ".join(f["column"] for f in insert_fields)
    insert_placeholders = ", ".join("?" for _ in insert_fields)
    insert_values = ", ".join(f'data["{f["name"]}"]' for f in insert_fields)

    if insert_fields and auto_inc:
        new_insert_exec = f"return insert(INSERT, ({insert_values},))"
    elif insert_fields:
        new_insert_exec = f"execute(INSERT, ({insert_values},))"
    else:
        new_insert_exec = "execute(INSERT)"

    # Un champ auto-généré (slug avec source) est stable à l'édition :
    # exclu de l'UPDATE (ADR-017 D4), mais conservé dans l'INSERT.
    update_fields = [f for f in non_pk if not _is_generated(f)]
    if update_fields:
        update_set = ", ".join(f'{f["column"]} = ?' for f in update_fields)
        update_values = ", ".join(f'data["{f["name"]}"]' for f in update_fields)
        update_constant = f'"UPDATE {table} SET {update_set} WHERE {pk_col} = ?"'
        update_exec = f"execute(UPDATE, ({update_values}, {pk_name}))"
    else:
        update_constant = "None  # aucun champ métier — UPDATE non applicable"
        update_exec = "return  # aucun champ à mettre à jour"

    lines: list[str] = [
        "from core.database.db import fetch_one, fetch_all, execute, insert",
        "",
        f'SELECT_ALL   = "{_build_select_base(table, relations)} ORDER BY {"" if not relations else table + "."}{pk_col}"',
        f'SELECT_BY_ID = "SELECT * FROM {table} WHERE {pk_col} = ?"',
        f'INSERT       = "INSERT INTO {table} ({insert_cols}) VALUES ({insert_placeholders})"',
        f'UPDATE       = {update_constant}',
        f'DELETE       = "DELETE FROM {table} WHERE {pk_col} = ?"',
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
        f"    execute(DELETE, ({pk_name},))",
        "",
        "",
        f"def bulk_delete_{plural}(ids):",
        '    """Supprime plusieurs enregistrements par ID. Aucune concaténation SQL."""',
        "    if not ids:",
        "        return",
        '    placeholders = ", ".join("?" for _ in ids)',
        f'    execute("DELETE FROM {table} WHERE {pk_col} IN (" + placeholders + ")", list(ids))',
        "",
    ]

    # ── Recherche, tri, pagination ────────────────────────────────────────────
    search_fields = _text_search_fields(definition, relations)
    qualifier = f"{table}." if relations else ""
    search_cols_repr = repr([qualifier + f["column"] for f in search_fields])
    sort_items = [(f["name"], qualifier + f["column"]) for f in non_pk]
    sort_items.append((pk_name, qualifier + pk_col))
    allowed_sort_repr = "{" + ", ".join(f'"{k}": "{v}"' for k, v in sort_items) + "}"
    filter_flds_model = _filter_fields(definition, relations)
    filter_items = [(f["name"], qualifier + f["column"]) for f in filter_flds_model]
    allowed_filters_repr = "{" + ", ".join(f'"{k}": "{v}"' for k, v in filter_items) + "}"

    lines.extend([
        "",
        f"_SEARCH_COLS  = {search_cols_repr}",
        f"_ALLOWED_SORT = {allowed_sort_repr}",
        f"_ALLOWED_FILTERS = {allowed_filters_repr}",
        f'_DEFAULT_SORT = "{qualifier}{pk_col}"',
        "",
        "",
        f"def count_{plural}(q=None, filters=None):",
        "    clauses = []",
        "    params = []",
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
        f'def find_{plural}_paginated(q=None, sort=None, direction="asc", limit=10, offset=0, filters=None):',
        "    sort_col = _ALLOWED_SORT.get(sort, _DEFAULT_SORT)",
        '    sort_dir = "DESC" if direction == "desc" else "ASC"',
        f'    base = "{_build_select_base(table, relations)}"',
        "    clauses = []",
        "    params = []",
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
        '        sql = base + " WHERE " + " AND ".join(clauses) + " ORDER BY " + sort_col + " " + sort_dir + " LIMIT ? OFFSET ?"',
        "    else:",
        '        sql = base + " ORDER BY " + sort_col + " " + sort_dir + " LIMIT ? OFFSET ?"',
        "    params.extend([limit, offset])",
        "    return fetch_all(sql, params)",
        "",
    ])
    lines.extend([
        "",
        "",
        "_EXPORT_LIMIT = 1000",
        "",
        "",
        f'def find_{plural}_for_export(q=None, sort=None, direction="asc", filters=None):',
        f"    return find_{plural}_paginated(",
        "        q=q, sort=sort, direction=direction,",
        "        limit=_EXPORT_LIMIT, offset=0, filters=filters,",
        "    )",
        "",
    ])
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
    return "\n".join(lines)
