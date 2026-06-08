"""Tests de la recherche HTMX optionnelle generee par forge make:crud."""

import json
from pathlib import Path

from forge_cli.entities.make_crud import (
    build_controller,
    build_index_view,
    build_model,
    build_results_partial,
    build_show_view,
    build_table_partial,
    make_crud,
)


def _field(
    name,
    sql_type,
    *,
    python_type,
    primary_key=False,
    auto_increment=False,
    nullable=False,
    list_filter=False,
):
    col = "".join(part.capitalize() for part in name.split("_") if part)
    field = {
        "name": name,
        "column": col,
        "python_type": python_type,
        "sql_type": sql_type,
        "nullable": nullable,
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


def _write_entity(root: Path, definition: dict) -> None:
    snake = definition["entity"].lower()
    entity_dir = root / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


_CONTACT_DISK = {
    "schema_version": "1.0",
    "name": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        {"name": "nom", "type": "string", "max_length": 100},
        {"name": "email", "type": "string", "max_length": 150, "nullable": True},
        {"name": "statut", "type": "string", "max_length": 50, "nullable": True},
    ],
}


def _run_contact(tmp_path: Path) -> None:
    entities_root = tmp_path / "mvc" / "entities"
    entity_dir = entities_root / "contact"
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / "contact.json").write_text(json.dumps(_CONTACT_DISK), encoding="utf-8")
    make_crud("Contact", entities_root=entities_root, output_root=tmp_path)


def _read(tmp_path: Path, path: str) -> str:
    return (tmp_path / path).read_text(encoding="utf-8")


def test_index_contient_cible_resultats_formulaire_get_et_attributs_htmx():
    html = build_index_view(CONTACT)

    assert '<div id="crud-results">' in html
    assert '{% include "contact/_results.html" %}' in html
    assert '<form method="get" action="/contact"' in html
    assert 'type="search"' in html
    assert 'name="q"' in html
    assert 'hx-get="/contact"' in html
    assert 'hx-target="#crud-results"' in html
    assert 'hx-swap="innerHTML"' in html
    assert 'hx-push-url="true"' in html


def test_index_ne_genere_pas_javascript_ni_recherche_live():
    html = build_index_view(CONTACT)

    assert "<script" not in html
    assert "keyup" not in html
    assert "delay:" not in html
    assert "hx-trigger" not in html


def test_results_partial_contient_table_et_pagination_sans_layout():
    html = build_results_partial(CONTACT)

    assert '{% include "contact/_table.html" %}' in html
    assert '{% include "contact/_pagination.html" %}' in html
    assert "extends" not in html
    assert "layouts/app.html" not in html


def test_make_crud_genere_results_partial_et_index_l_inclut(tmp_path):
    _run_contact(tmp_path)

    assert (tmp_path / "mvc" / "views" / "contact" / "_results.html").exists()
    index = _read(tmp_path, "mvc/views/contact/index.html")
    results = _read(tmp_path, "mvc/views/contact/_results.html")

    assert '<div id="crud-results">' in index
    assert '{% include "contact/_results.html" %}' in index
    assert '{% include "contact/_table.html" %}' in results
    assert '{% include "contact/_pagination.html" %}' in results


def test_controller_detecte_hx_request_et_choisit_le_partial():
    code = build_controller(CONTACT)

    assert "def _is_hx_request(request):" in code
    assert 'request.headers.get("HX-Request", "").lower() == "true"' in code
    assert 'template = "contact/_results.html" if _is_hx_request(request) else "contact/index.html"' in code
    assert "BaseController.render(template, context=context, request=request)" in code


def test_controller_transmet_q_filters_sort_direction_au_contexte():
    code = build_controller(CONTACT)

    assert 'q         = _query_param(request, "q").strip()' in code
    assert '"q": q, "sort": sort, "direction": direction,' in code
    assert '"filters": {"statut": statut_f}' in code
    assert 'total    = count_contacts(q or None, filters=_filters or None)' in code
    assert "q=q or None, sort=sort or None, direction=direction," in code
    assert "filters=_filters or None" in code


def test_recherche_sql_filtres_tri_et_pagination_restent_classiques():
    model = build_model(CONTACT)

    assert 'clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")' in model
    assert 'params.extend("%" + q + "%" for _ in _SEARCH_COLS)' in model
    assert '_ALLOWED_FILTERS.get(key)' in model
    assert 'clauses.append(col + " = ?")' in model
    assert "ORDER BY \" + sort_col + \" \" + sort_dir" in model
    assert "LIMIT ? OFFSET ?" in model
    assert "hx-" not in model


def test_pas_de_htmx_sur_suppression():
    table = build_table_partial(CONTACT)

    assert "hx-delete" not in table
    assert 'method="post"' in table
    assert "onsubmit" in table


def test_create_edit_show_delete_et_auth_rbac_restent_hors_perimetre():
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
