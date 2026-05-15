"""Tests du tri simple genere par forge make:crud."""

from forge_cli.entities.make_crud import (
    CrudManyToManyRelation,
    CrudManyToOneRelation,
    build_controller,
    build_index_view,
    build_model,
    build_pagination_partial,
    build_table_partial,
)


def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False):
    col = "".join(part.capitalize() for part in name.split("_") if part)
    return {
        "name": name,
        "column": col,
        "python_type": python_type,
        "sql_type": sql_type,
        "nullable": False,
        "primary_key": primary_key,
        "auto_increment": auto_increment,
        "constraints": {},
        "unique": False,
    }


CONTACT = {
    "format_version": 1,
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
        _field("email", "VARCHAR(150)", python_type="str"),
    ],
}

CONTACT_WITH_FILTER = {
    "format_version": 1,
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
        {**_field("statut", "VARCHAR(50)", python_type="str"), "list": {"filter": True}},
    ],
}

CONTACT_WITH_VILLE = {
    "format_version": 1,
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
        _field("ville_id", "INT", python_type="int"),
    ],
}


def _ville_relation():
    return CrudManyToOneRelation(
        field_name="ville_id",
        field_column="VilleId",
        target_entity="Ville",
        target_table="ville",
        target_pk_column="Id",
        target_label_column="Nom",
        choices_function="get_ville_choices",
        choices_key="ville_id_choices",
    )


def _tag_relation():
    return CrudManyToManyRelation(
        source="article",
        target="tag",
        pivot_table="article_tag",
        source_key="article_id",
        target_key="tag_id",
        target_entity="Tag",
        target_table="tag",
        target_pk_column="Id",
        target_label_column="Nom",
        field_name="tag_ids",
        choices_function="get_tag_choices",
        choices_key="tag_choices",
        selected_function="get_article_tag_ids",
        add_function="add_article_tag_ids",
        sync_function="sync_article_tag_ids",
        list_labels_function="get_article_tag_labels_by_article_id",
        show_labels_function="get_article_tag_labels",
        list_context_key="tags_by_article_id",
        selected_key="tag_ids_selected",
        show_context_key="tag_labels",
    )


def test_controller_lit_sort_et_direction():
    code = build_controller(CONTACT)

    assert '_query_param(request, "sort")' in code
    assert '_query_param(request, "direction", "desc")' in code


def test_direction_invalide_revient_a_asc():
    code = build_controller(CONTACT)

    assert 'if direction not in ("asc", "desc"):' in code
    assert 'direction = "asc"' in code


def test_sort_invalide_est_ignore_par_le_controller():
    code = build_controller(CONTACT)

    assert 'if sort not in {"nom", "email", "id"}:' in code
    assert 'sort = ""' in code


def test_order_by_utilise_allowlist_de_colonnes():
    code = build_model(CONTACT)

    assert '_ALLOWED_SORT = {"nom": "Nom", "email": "Email", "id": "Id"}' in code
    assert "sort_col = _ALLOWED_SORT.get(sort, _DEFAULT_SORT)" in code
    assert 'ORDER BY " + sort_col + " " + sort_dir' in code


def test_sort_pas_concatene_directement_depuis_get():
    code = build_model(CONTACT)

    assert '" + sort + "' not in code
    assert ".format(sort" not in code
    assert "sort_col = _ALLOWED_SORT.get(sort, _DEFAULT_SORT)" in code


def test_direction_pas_concatenee_directement_depuis_get():
    code = build_model(CONTACT)

    assert 'sort_dir = "DESC" if direction == "desc" else "ASC"' in code
    assert '" + direction' not in code


def test_liens_de_tri_presents_dans_index():
    html = build_table_partial(CONTACT)

    assert "?sort=nom" in html
    assert "?sort=email" in html
    assert "pagination.direction == 'asc'" in html
    assert "'desc' if pagination.direction == 'asc' else 'asc'" in html


def test_liens_de_tri_conservent_q_et_filters():
    html = build_table_partial(CONTACT_WITH_FILTER)

    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in html
    assert "pagination.filters.items()" in html
    assert "&amp;{{ key }}={{ val | urlencode }}" in html


def test_pagination_conserve_sort_et_direction():
    html = build_pagination_partial(CONTACT)

    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in html
    assert "page={{ pagination.page - 1 }}" in html
    assert "page={{ pagination.page + 1 }}" in html


def test_tri_compatible_avec_q_et_filtres_simples():
    code = build_controller(CONTACT_WITH_FILTER)

    assert "q=q or None, sort=sort or None, direction=direction," in code
    assert "filters=_filters or None" in code
    assert '"sort": sort, "direction": direction' in code
    assert '"filters": {"statut": statut_f}' in code


def test_tri_compatible_avec_filtre_many_to_one():
    code = build_controller(CONTACT_WITH_VILLE, [_ville_relation()])
    html = build_table_partial(CONTACT_WITH_VILLE, [_ville_relation()])

    assert '_filters["ville_id"] = ville_id_f' in code
    assert "q=q or None, sort=sort or None, direction=direction," in code
    assert "?sort=ville_id" in html
    assert "pagination.filters.items()" in html


def test_pas_de_tri_many_to_many():
    html = build_table_partial(CONTACT, many_to_many_relations=[_tag_relation()])

    assert "?sort=tag_ids" not in html
    assert "?sort=tag" not in html
    assert "tags_by_article_id" in html


def test_aucun_javascript_ajoute():
    html = build_index_view(CONTACT)

    assert "<script" not in html
