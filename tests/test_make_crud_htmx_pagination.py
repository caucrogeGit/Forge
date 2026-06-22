"""Tests de la pagination HTMX optionnelle generee par forge make:crud."""

from pathlib import Path

from cli.entities.make_crud import (
    build_controller,
    build_model,
    build_pagination_partial,
    build_results_partial,
    build_show_view,
    build_table_partial,
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


def test_pagination_garde_href_classique_et_ajoute_htmx_progressif():
    html = build_pagination_partial(CONTACT)

    assert '<a href="?page={{ pagination.page - 1 }}' in html
    assert '<a href="?page={{ pagination.page + 1 }}' in html
    assert 'hx-get="?page={{ pagination.page - 1 }}' in html
    assert 'hx-get="?page={{ pagination.page + 1 }}' in html
    assert 'hx-target="#crud-results"' in html
    assert 'hx-swap="innerHTML"' in html
    assert 'hx-push-url="true"' in html


def test_hx_get_reprend_la_meme_construction_url_que_href():
    html = build_pagination_partial(CONTACT)

    prev = "?page={{ pagination.page - 1 }}"
    next_ = "?page={{ pagination.page + 1 }}"
    q = "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}"
    sort = "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}"

    assert f'href="{prev}{q}{sort}' in html
    assert f'hx-get="{prev}{q}{sort}' in html
    assert f'href="{next_}{q}{sort}' in html
    assert f'hx-get="{next_}{q}{sort}' in html


def test_pagination_conserve_q_filtres_sort_direction():
    html = build_pagination_partial(CONTACT)

    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in html
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in html
    assert "pagination.filters.items()" in html
    assert "&amp;{{ key }}={{ val | urlencode }}" in html


def test_results_partial_inclut_toujours_la_pagination():
    html = build_results_partial(CONTACT)

    assert '{% include "contact/_table.html" %}' in html
    assert '{% include "contact/_pagination.html" %}' in html
    assert "extends" not in html


def test_controller_rend_results_sur_hx_request_et_index_sinon():
    code = build_controller(CONTACT)

    assert 'request.headers.get("HX-Request", "").lower() == "true"' in code
    assert 'template = "contact/_results.html" if _is_hx_request(request) else "contact/index.html"' in code
    assert "BaseController.render(template, context=context, request=request)" in code


def test_pas_de_js_recherche_live_ni_hx_delete():
    pagination = build_pagination_partial(CONTACT)
    table = build_table_partial(CONTACT)

    assert "<script" not in pagination
    assert "hx-trigger" not in pagination
    assert "keyup" not in pagination
    assert "hx-delete" not in table
    assert 'method="post"' in table
    assert "onsubmit" in table


def test_create_edit_show_delete_et_auth_rbac_hors_perimetre():
    code = build_controller(CONTACT)
    show = build_show_view(CONTACT)

    assert "def new(request: Request) -> Response:" in code
    assert "def create(request: Request) -> Response:" in code
    assert "def edit(request: Request) -> Response:" in code
    assert "def update(request: Request) -> Response:" in code
    assert "def destroy(request: Request) -> Response:" in code
    assert "HX-Request" not in show
    assert "require_user_permission" not in code
    assert "auth" not in code.lower()


def test_pagination_core_et_sql_restent_inchanges():
    pagination_core = Path("core/mvc/view/pagination.py").read_text(encoding="utf-8")
    model = build_model(CONTACT)
    controller = build_controller(CONTACT)

    assert "class Pagination" in pagination_core
    assert "pagination_state = Pagination(request, total, limit)" in controller
    assert "limit = pagination_state.limit" in controller
    assert "offset = pagination_state.offset" in controller
    assert 'clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")' in model
    assert 'clauses.append(col + " = ?")' in model
    assert "ORDER BY \" + sort_col + \" \" + sort_dir" in model
    assert "LIMIT ? OFFSET ?" in model
