"""Tests de la pagination CRUD generee par forge make:crud."""

from cli.entities.make_crud import (
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


def test_controller_utilise_pagination_core():
    code = build_controller(CONTACT)

    assert "from core.mvc.view.pagination import Pagination" in code
    assert "pagination_state = Pagination(request, total, limit)" in code


def test_page_absente_invalide_ou_negative_est_gerree_par_pagination_core():
    code = build_controller(CONTACT)

    assert '_query_param(request, "page", 1)' not in code
    assert "Pagination(request, total, limit)" in code
    assert "page = 1" not in code
    assert "page = max(1" not in code


def test_limit_et_offset_viennent_de_pagination_core():
    code = build_controller(CONTACT)

    assert "limit  = 20" in code
    assert "limit = pagination_state.limit" in code
    assert "offset = pagination_state.offset" in code
    assert "offset = (page - 1) * limit" not in code


def test_model_count_et_find_paginated_conservent_limit_offset():
    code = build_model(CONTACT)

    assert "def count_contacts(q=None, filters=None):" in code
    assert 'def find_contacts_paginated(q=None, sort=None, direction="asc", limit=10, offset=0, filters=None):' in code
    assert "LIMIT ? OFFSET ?" in code
    assert "params.extend([limit, offset])" in code


def test_count_et_find_recoivent_q():
    code = build_controller(CONTACT)

    assert "total    = count_contacts(q or None)" in code
    assert "q=q or None, sort=sort or None, direction=direction," in code


def test_count_et_find_recoivent_filters_si_presents():
    code = build_controller(CONTACT_WITH_FILTER)

    assert "total    = count_contacts(q or None, filters=_filters or None)" in code
    assert "limit=limit, offset=offset, filters=_filters or None," in code


def test_find_recoit_sort_et_direction():
    code = build_controller(CONTACT)

    assert "q=q or None, sort=sort or None, direction=direction," in code


def test_contexte_pagination_contient_q_filters_sort_direction():
    code = build_controller(CONTACT_WITH_FILTER)

    assert "pagination = pagination_state.to_dict()" in code
    assert 'pagination.update({' in code
    assert '"q": q, "sort": sort, "direction": direction,' in code
    assert '"filters": {"statut": statut_f}' in code


def test_template_index_contient_liens_pagination():
    html = build_pagination_partial(CONTACT)

    assert "{% if pagination.nb_pages > 1 %}" in html
    assert "page={{ pagination.page - 1 }}" in html
    assert "page={{ pagination.page + 1 }}" in html
    assert "pagination.has_prev" in html
    assert "pagination.has_next" in html


def test_liens_pagination_conservent_q_filters_sort_direction():
    html = build_pagination_partial(CONTACT_WITH_FILTER)

    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in html
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in html
    assert "pagination.filters.items()" in html
    assert "&amp;{{ key }}={{ val | urlencode }}" in html


def test_pagination_compatible_filtre_many_to_one():
    code = build_controller(CONTACT_WITH_VILLE, [_ville_relation()])
    index_html = build_index_view(CONTACT_WITH_VILLE, [_ville_relation()])
    pagination_html = build_pagination_partial(CONTACT_WITH_VILLE)

    assert '_filters["ville_id"] = ville_id_f' in code
    assert "pagination_state = Pagination(request, total, limit)" in code
    assert '"filters": {"ville_id": ville_id_f}' in code
    assert "pagination.filters.ville_id" in index_html
    assert "pagination.filters.items()" in pagination_html


def test_pagination_compatible_tri():
    table_html = build_table_partial(CONTACT)
    pagination_html = build_pagination_partial(CONTACT)

    assert "?sort=nom" in table_html
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in pagination_html


def test_aucun_javascript_ajoute():
    html = build_index_view(CONTACT)

    assert "<script" not in html
