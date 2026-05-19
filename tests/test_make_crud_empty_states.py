"""Tests des états vides contextuels du CRUD généré."""

import json
from pathlib import Path

from forge_cli.entities.make_crud import (
    CrudManyToManyRelation,
    CrudManyToOneRelation,
    build_controller,
    build_index_view,
    build_model,
    build_pagination_partial,
    build_show_view,
    build_table_partial,
)


def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False):
    column = "".join(part.capitalize() for part in name.split("_") if part)
    return {
        "name": name,
        "column": column,
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


CONTACT_WITH_BOOL_FILTER = {
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
        {**_field("actif", "BOOLEAN", python_type="bool"), "list": {"filter": True}},
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


def _tag_relation():
    return CrudManyToManyRelation(
        source="contact",
        target="tag",
        pivot_table="contact_tag",
        source_key="contact_id",
        target_key="tag_id",
        target_entity="Tag",
        target_table="tag",
        target_pk_column="Id",
        target_label_column="Nom",
        field_name="tag_ids",
        choices_function="get_tag_choices",
        choices_key="tag_choices",
        selected_function="get_contact_tag_ids",
        add_function="add_contact_tag_ids",
        sync_function="sync_contact_tag_ids",
        list_labels_function="get_contact_tag_labels_by_contact_id",
        show_labels_function="get_contact_tag_labels",
        list_context_key="tags_by_contact_id",
        selected_key="tag_ids_selected",
        show_context_key="tag_labels",
    )


def test_etat_vide_general_existant_est_conserve():
    html = build_table_partial(CONTACT)

    assert "border-dashed" in html
    assert "trans('crud.empty')" in html


def test_controller_calcule_empty_context_default_sans_q_ni_filtres():
    code = build_controller(CONTACT)

    assert 'empty_context = "search" if q else None' in code
    assert '"empty_context": empty_context' in code


def test_q_non_vide_active_empty_context_search():
    code = build_controller(CONTACT)

    assert 'empty_context = "search" if q else None' in code
    assert 'q         = _query_param(request, "q").strip()' in code


def test_q_vide_apres_strip_n_active_pas_search():
    code = build_controller(CONTACT)

    assert 'q         = _query_param(request, "q").strip()' in code
    assert 'empty_context = "search" if q else None' in code


def test_filtre_valide_actif_active_empty_context_filters():
    code = build_controller(CONTACT_WITH_FILTER)

    assert 'if statut_f != "":' in code
    assert '_filters["statut"] = statut_f' in code
    assert '"filters" if _filters else None' in code


def test_filtre_vide_n_active_pas_filters():
    code = build_controller(CONTACT_WITH_FILTER)

    assert 'statut_f = _query_param(request, "statut").strip()' in code
    assert 'if statut_f != "":' in code
    assert '"filters" if _filters else None' in code


def test_filtre_invalide_ignore_n_active_pas_filters():
    code = build_controller(CONTACT_WITH_BOOL_FILTER)

    assert 'if actif_f in ("0", "1"):' in code
    assert '_filters["actif"] = actif_f' in code
    assert '"filters" if _filters else None' in code


def test_filtre_relationnel_invalide_ignore_n_active_pas_filters():
    code = build_controller(CONTACT_WITH_VILLE, [_ville_relation()])

    assert 'ville_id_raw = _query_param(request, "ville_id").strip()' in code
    assert 'ville_id_f = ""' in code
    assert '_filters["ville_id"] = ville_id_f' in code


def test_q_et_filtre_valide_activent_empty_context_search_filters():
    code = build_controller(CONTACT_WITH_FILTER)

    assert 'empty_context = "search_filters" if q and _filters else ("search" if q else ("filters" if _filters else None))' in code


def test_template_index_affiche_messages_contextuels():
    html = build_table_partial(CONTACT_WITH_FILTER)

    assert 'empty_context == "search"' in html
    assert "trans('crud.empty_search')" in html
    assert 'empty_context == "filters"' in html
    assert "trans('crud.empty_filters')" in html
    assert 'empty_context == "search_filters"' in html
    assert "trans('crud.empty_search_filters')" in html
    assert "trans('crud.empty')" in html


def test_cles_i18n_contextuelles_existent():
    catalog = json.loads(Path("translations/fr.json").read_text(encoding="utf-8"))

    assert catalog["crud.empty_search"] == "Aucun résultat ne correspond à votre recherche."
    assert catalog["crud.empty_filters"] == "Aucun résultat ne correspond aux filtres sélectionnés."
    assert (
        catalog["crud.empty_search_filters"]
        == "Aucun résultat ne correspond à votre recherche et aux filtres sélectionnés."
    )


def test_q_filtres_pagination_et_tri_restent_conserves():
    index_html = build_index_view(CONTACT_WITH_FILTER)
    table_html = build_table_partial(CONTACT_WITH_FILTER)
    pagination_html = build_pagination_partial(CONTACT_WITH_FILTER)
    code = build_controller(CONTACT_WITH_FILTER)

    assert 'value="{{ pagination.q }}"' in index_html
    assert "pagination.filters.statut" in index_html
    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in pagination_html
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in pagination_html
    assert "pagination.filters.items()" in table_html
    assert '"q": q, "sort": sort, "direction": direction,' in code
    assert '"filters": {"statut": statut_f}' in code


def test_recherche_sql_et_filtres_sql_restent_inchanges():
    model = build_model(CONTACT_WITH_FILTER)

    assert "LIKE ?" in model
    assert 'params.extend("%" + q + "%" for _ in _SEARCH_COLS)' in model
    assert "for key, val in (filters or {}).items():" in model
    assert '_ALLOWED_FILTERS.get(key)' in model
    assert 'clauses.append(col + " = ?")' in model
    assert "LIMIT ? OFFSET ?" in model


def test_many_to_many_vide_list_show_reste_inchange():
    relation = _tag_relation()
    index_html = build_table_partial(CONTACT, many_to_many_relations=[relation])
    show_html = build_show_view(CONTACT, many_to_many_relations=[relation])

    assert '| join(", ") if _tag_ids_labels else "—"' in index_html
    assert "Aucun Tag" in show_html


def test_aucun_js_auth_rbac_ajoute():
    generated = "\n".join([
        build_controller(CONTACT_WITH_FILTER),
        build_index_view(CONTACT_WITH_FILTER),
    ])

    assert "<script" not in generated
    assert "require_user_permission" not in generated
    assert "auth" not in generated.lower()
