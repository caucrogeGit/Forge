"""Tests des partials CRUD prepares pour HTMX, sans activer HTMX."""

import json
from pathlib import Path

from forge_cli.entities.make_crud import make_crud, _to_snake


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


ARTICLE = {
    "entity": "Article",
    "table": "article",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("title", "VARCHAR(150)", python_type="str"),
        _field("status", "VARCHAR(50)", python_type="str", list_filter=True),
        _field("category_id", "INT", python_type="int", nullable=True),
    ],
}


TAG = {
    "entity": "Tag",
    "table": "tag",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("name", "VARCHAR(80)", python_type="str"),
    ],
}


CATEGORY = {
    "entity": "Category",
    "table": "category",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("title", "VARCHAR(80)", python_type="str"),
    ],
}


RELATIONS = {
    "schema_version": "1.0",
    "relations": [
        {
            "type": "many_to_one",
            "from": "Article",
            "to": "Category",
            "name": "article_category",
            "foreign_key": "category_id",
            "nullable": True,
            "on_delete": "set_null",
        },
        {
            "type": "many_to_many",
            "from": "Article",
            "to": "Tag",
            "name": "tags",
            "pivot": {
                "table": "article_tag",
                "from_key": "article_id",
                "to_key": "tag_id",
                "id": True,
                "unique_pair": True,
                "on_delete": "cascade",
                "fields": [],
            },
        },
    ],
}


def _write_entity(root: Path, definition: dict) -> None:
    snake = _to_snake(definition["entity"])
    entity_dir = root / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


def _run_article(tmp_path: Path) -> None:
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, ARTICLE)
    _write_entity(entities_root, TAG)
    _write_entity(entities_root, CATEGORY)
    (entities_root / "relations.json").write_text(json.dumps(RELATIONS), encoding="utf-8")
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)


def _read(tmp_path: Path, path: str) -> str:
    return (tmp_path / path).read_text(encoding="utf-8")


def test_make_crud_genere_partials_liste_et_pagination(tmp_path):
    _run_article(tmp_path)

    assert (tmp_path / "mvc" / "views" / "article" / "_table.html").exists()
    assert (tmp_path / "mvc" / "views" / "article" / "_pagination.html").exists()


def test_index_inclut_les_partials_et_conserve_recherche_filtres(tmp_path):
    _run_article(tmp_path)

    index = _read(tmp_path, "mvc/views/article/index.html")

    assert '{% include "article/_results.html" %}' in index
    assert '<form method="get"' in index
    assert 'type="search"' in index
    assert 'name="q"' in index
    assert 'name="status"' in index
    assert 'name="category_id"' in index
    assert "<table" not in index
    assert "pagination.nb_pages" not in index


def test_table_partial_contient_table_actions_tri_etats_vides_et_relations(tmp_path):
    _run_article(tmp_path)

    table = _read(tmp_path, "mvc/views/article/_table.html")

    assert "<table" in table
    assert "?sort=title" in table
    assert "?sort=category_id" in table
    assert "trans('crud.actions')" in table
    assert "trans('crud.show')" in table
    assert "trans('crud.edit')" in table
    assert "trans('crud.delete')" in table
    assert "onsubmit" in table
    assert "return confirm(" in table
    assert 'empty_context == "search"' in table
    assert "trans('crud.empty_search')" in table
    assert 'empty_context == "filters"' in table
    assert "trans('crud.empty_filters')" in table
    assert 'empty_context == "search_filters"' in table
    assert "trans('crud.empty_search_filters')" in table
    assert "trans('crud.empty')" in table
    assert "article.category_id_label" in table
    assert "tags_by_article_id.get(article.Id, [])" in table
    assert '| join(", ") if _tag_ids_labels else "—"' in table


def test_pagination_partial_conserve_q_filtres_sort_direction(tmp_path):
    _run_article(tmp_path)

    pagination = _read(tmp_path, "mvc/views/article/_pagination.html")

    assert "{% if pagination.nb_pages > 1 %}" in pagination
    assert "pagination.has_prev" in pagination
    assert "pagination.has_next" in pagination
    assert "page={{ pagination.page - 1 }}" in pagination
    assert "page={{ pagination.page + 1 }}" in pagination
    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in pagination
    assert "{% if pagination.sort %}&amp;sort={{ pagination.sort | urlencode }}&amp;direction={{ pagination.direction }}{% endif %}" in pagination
    assert "pagination.filters.items()" in pagination
    assert "&amp;{{ key }}={{ val | urlencode }}" in pagination


def test_partials_ne_changent_pas_create_edit_show_delete_ni_sql(tmp_path):
    _run_article(tmp_path)

    controller = _read(tmp_path, "mvc/controllers/article_controller.py")
    model = _read(tmp_path, "mvc/models/article_model.py")
    form = _read(tmp_path, "mvc/views/article/form.html")
    show = _read(tmp_path, "mvc/views/article/show.html")

    assert 'else "article/index.html"' in controller
    assert "HX-Request" in controller
    assert "def create(request):" in controller
    assert "def edit(request):" in controller
    assert "def update(request):" in controller
    assert "def destroy(request):" in controller
    assert "LIKE ?" in model
    assert "LIMIT ? OFFSET ?" in model
    assert 'name="tag_ids"' in form
    assert "tag_labels | join" in show


def test_aucun_javascript_auth_ou_rbac_n_est_genere(tmp_path):
    _run_article(tmp_path)

    generated = "\n".join(
        _read(tmp_path, path)
        for path in (
            "mvc/controllers/article_controller.py",
            "mvc/models/article_model.py",
            "mvc/views/article/_table.html",
            "mvc/views/article/_pagination.html",
            "mvc/views/article/_results.html",
            "mvc/views/article/form.html",
            "mvc/views/article/show.html",
        )
    )

    assert "hx-delete" not in generated
    assert "hx-trigger" not in generated
    assert "<script" not in generated
    assert "require_user_permission" not in generated
    assert "auth" not in generated.lower()
