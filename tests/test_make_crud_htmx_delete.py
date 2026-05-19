"""Tests de la suppression HTMX optionnelle generee par forge make:crud."""

from forge_cli.entities.make_crud import (
    build_controller,
    build_index_view,
    build_model,
    build_pagination_partial,
    build_table_partial,
    build_show_view,
)


def _field(name, sql_type, *, python_type, primary_key=False, auto_increment=False, list_filter=False):
    col = "".join(part.capitalize() for part in name.split("_") if part)
    field = {
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
    if list_filter:
        field["list"] = {"filter": True}
    return field


CONTACT = {
    "entity": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
        _field("email", "VARCHAR(150)", python_type="str"),
        _field("statut", "VARCHAR(50)", python_type="str", list_filter=True),
    ],
}


def test_formulaire_suppression_garde_fallback_html_csrf_et_action():
    html = build_table_partial(CONTACT)

    assert '<form method="post" action="/contacts/{{ contact.Id }}/delete' in html
    assert 'name="csrf_token" value="{{ csrf_token }}"' in html
    assert '<button type="submit"' in html
    assert "onsubmit=\"return confirm(" in html


def test_formulaire_suppression_ajoute_htmx_sur_meme_url_que_action():
    html = build_table_partial(CONTACT)

    action = (
        '/contacts/{{ contact.Id }}/delete?page={{ pagination.page }}'
        "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}"
    )
    assert f'action="{action}' in html
    assert f'hx-post="{action}' in html
    assert 'hx-target="#crud-results"' in html
    assert 'hx-swap="innerHTML"' in html
    assert 'hx-confirm="{{ trans(\'crud.confirm_delete\') }}"' in html


def test_suppression_preserve_parametres_liste_dans_url():
    html = build_table_partial(CONTACT)

    assert "?page={{ pagination.page }}" in html
    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in html
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in html
    assert "pagination.filters.items()" in html
    assert "&amp;{{ key }}={{ val | urlencode }}" in html


def test_destroy_classique_redirige_et_hx_rend_results():
    code = build_controller(CONTACT)

    assert 'delete_contact(id)' in code
    assert 'if _is_hx_request(request):' in code
    assert 'context = ContactController._list_context(request)' in code
    assert 'return BaseController.render("contact/_results.html", context=context, request=request)' in code
    assert 'return BaseController.redirect_with_flash(request, "/contacts", "Contact supprimé.")' in code


def test_destroy_hx_ne_rend_pas_index_complet():
    code = build_controller(CONTACT)
    destroy_block = code[code.index("    def destroy(request):"):]

    assert '"contact/_results.html"' in destroy_block
    assert '"contact/index.html"' not in destroy_block
    assert 'layouts/app.html' not in destroy_block


def test_destroy_reutilise_contexte_liste_sans_modifier_pagination_sql():
    controller = build_controller(CONTACT)
    model = build_model(CONTACT)

    assert "def _list_context(request):" in controller
    assert "pagination_state = Pagination(request, total, limit)" in controller
    assert "limit = pagination_state.limit" in controller
    assert "offset = pagination_state.offset" in controller
    assert 'clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")' in model
    assert 'clauses.append(col + " = ?")' in model
    assert "ORDER BY \" + sort_col + \" \" + sort_dir" in model
    assert "LIMIT ? OFFSET ?" in model


def test_pas_de_hx_delete_ni_javascript_personnalise():
    html = "\n".join([
        build_table_partial(CONTACT),
        build_index_view(CONTACT),
        build_pagination_partial(CONTACT),
    ])

    assert "hx-delete" not in html
    assert "<script" not in html
    assert "keyup" not in html
    assert "hx-trigger" not in html


def test_method_override_absent_reste_absent_car_route_post():
    html = build_table_partial(CONTACT)
    route_block = build_controller(CONTACT)

    assert 'method="post"' in html
    assert 'name="_method"' not in html
    assert 'def destroy(request):' in route_block


def test_recherche_pagination_create_edit_show_hors_perimetre():
    controller = build_controller(CONTACT)
    show = build_show_view(CONTACT)
    index = build_index_view(CONTACT)
    pagination = build_pagination_partial(CONTACT)

    assert 'hx-get="/contacts"' in index
    assert 'hx-get="?page={{ pagination.page - 1 }}' in pagination
    assert 'hx-get="?page={{ pagination.page + 1 }}' in pagination
    assert "def new(request):" in controller
    assert "def create(request):" in controller
    assert "def edit(request):" in controller
    assert "def update(request):" in controller
    assert "HX-Request" not in show
    assert "require_user_permission" not in controller
    assert "auth" not in controller.lower()
