"""Tests de forge make:crud pour les formulaires many_to_many."""

import json
from pathlib import Path

from forge_mvc_entities.make_crud import make_crud, _to_snake


def _field(
    name,
    sql_type,
    *,
    python_type,
    primary_key=False,
    auto_increment=False,
    nullable=False,
    constraints=None,
):
    col = "".join(p.capitalize() for p in name.split("_") if p)
    return {
        "name": name,
        "column": col,
        "python_type": python_type,
        "sql_type": sql_type,
        "nullable": nullable,
        "primary_key": primary_key,
        "auto_increment": auto_increment,
        "constraints": constraints or {},
        "unique": False,
    }


ARTICLE_JSON = {
    "entity": "Article",
    "table": "article",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("title", "VARCHAR(150)", python_type="str"),
        _field("category_id", "INT", python_type="int", nullable=True),
    ],
}


TAG_JSON = {
    "entity": "Tag",
    "table": "tag",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("name", "VARCHAR(80)", python_type="str"),
    ],
}


CATEGORY_JSON = {
    "entity": "Category",
    "table": "category",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("title", "VARCHAR(80)", python_type="str"),
    ],
}


def _write_entity(tmp_path: Path, definition: dict) -> None:
    snake = _to_snake(definition["entity"])
    entity_dir = tmp_path / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


def _canonical_m2m(from_entity: str, to_entity: str, name: str, pivot_table: str,
                   from_key: str, to_key: str) -> dict:
    return {
        "type": "many_to_many",
        "from": from_entity,
        "to": to_entity,
        "name": name,
        "pivot": {
            "table": pivot_table,
            "from_key": from_key,
            "to_key": to_key,
            "id": True,
            "unique_pair": True,
            "on_delete": "cascade",
            "fields": [],
        },
    }


def _canonical_m2o(from_entity: str, to_entity: str, name: str, foreign_key: str,
                   on_delete: str = "restrict", nullable: bool = False) -> dict:
    return {
        "type": "many_to_one",
        "from": from_entity,
        "to": to_entity,
        "name": name,
        "foreign_key": foreign_key,
        "nullable": nullable,
        "on_delete": on_delete,
    }


def _relations(*extra_relations: dict) -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            _canonical_m2m("Article", "Tag", "tags", "article_tag", "article_id", "tag_id"),
            *extra_relations,
        ],
    }


def _run_article(tmp_path: Path, relations: dict | None = None) -> None:
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(tmp_path, ARTICLE_JSON)
    _write_entity(tmp_path, TAG_JSON)
    _write_entity(tmp_path, CATEGORY_JSON)
    if relations is None:
        relations = _relations()
    (entities_root / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)


def _read(tmp_path: Path, path: str) -> str:
    return (tmp_path / path).read_text(encoding="utf-8")


def test_make_crud_detecte_many_to_many_source_et_genere_select_multiple(tmp_path):
    _run_article(tmp_path)

    form_html = _read(tmp_path, "mvc/views/article/form.html")

    assert "<select" in form_html
    assert "multiple" in form_html
    assert 'name="tag_ids"' in form_html
    assert "{% for value, label in tag_choices %}" in form_html
    assert "tag_ids_selected" in form_html


def test_make_crud_ignore_many_to_many_cote_target(tmp_path):
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(tmp_path, ARTICLE_JSON)
    _write_entity(tmp_path, TAG_JSON)
    (entities_root / "relations.json").write_text(json.dumps(_relations()), encoding="utf-8")

    make_crud("Tag", entities_root=entities_root, output_root=tmp_path)

    form_html = _read(tmp_path, "mvc/views/tag/form.html")
    assert 'name="article_ids"' not in form_html
    assert 'name="tag_ids"' not in form_html


def test_controller_charge_choix_target_et_ids_existants_pour_edit(tmp_path):
    _run_article(tmp_path)

    controller = _read(tmp_path, "mvc/controllers/article_controller.py")

    assert "get_tag_choices()" in controller
    assert "get_article_tag_ids(id)" in controller
    assert '"tag_choices": get_tag_choices(),' in controller
    assert '"tag_ids_selected": get_article_tag_ids(id),' in controller


def test_controller_extrait_et_deduplique_les_ids_multiples(tmp_path):
    _run_article(tmp_path)

    controller = _read(tmp_path, "mvc/controllers/article_controller.py")

    assert "def _parse_many_ids(request, field_name):" in controller
    assert "raw = request.body.get(field_name, [])" in controller
    assert "item = int(value)" in controller
    assert "if item <= 0 or item in seen:" in controller
    assert "seen.add(item)" in controller
    assert 'tag_ids = ArticleController._parse_many_ids(request, "tag_ids")' in controller


def test_model_insere_le_pivot_a_la_creation_et_synchronise_a_l_edition(tmp_path):
    _run_article(tmp_path)

    model = _read(tmp_path, "mvc/models/article_model.py")
    controller = _read(tmp_path, "mvc/controllers/article_controller.py")

    assert "def add_article_tag_ids(id, selected_ids):" in model
    assert "INSERT INTO article_tag (article_id, tag_id) VALUES (?, ?)" in model
    assert "def sync_article_tag_ids(id, selected_ids):" in model
    assert "DELETE FROM article_tag WHERE article_id = ?" in model
    assert "add_article_tag_ids(created_id, tag_ids)" in controller
    assert "sync_article_tag_ids(id, tag_ids)" in controller


def test_plusieurs_relations_many_to_many_generent_plusieurs_selects(tmp_path):
    _run_article(
        tmp_path,
        relations=_relations(
            _canonical_m2m("Article", "Category", "categories", "article_category", "article_id", "category_id")
        ),
    )

    form_html = _read(tmp_path, "mvc/views/article/form.html")
    model = _read(tmp_path, "mvc/models/article_model.py")

    assert 'name="tag_ids"' in form_html
    assert 'name="category_ids"' in form_html
    assert "INSERT INTO article_tag (article_id, tag_id) VALUES (?, ?)" in model
    assert "INSERT INTO article_category (article_id, category_id) VALUES (?, ?)" in model


def test_relations_many_to_one_et_champs_classiques_restent_supportes(tmp_path):
    _run_article(
        tmp_path,
        relations=_relations(
            _canonical_m2o("Article", "Category", "article_category", "category_id",
                           on_delete="set_null", nullable=True)
        ),
    )

    form_code = _read(tmp_path, "mvc/forms/article_form.py")
    form_html = _read(tmp_path, "mvc/views/article/form.html")

    assert "RelationField" in form_code
    assert "select_field(name='category_id'" in form_html
    assert "field(name='title'" in form_html
    assert 'name="tag_ids"' in form_html


def test_list_show_affichent_les_libelles_many_to_many(tmp_path):
    _run_article(tmp_path)

    controller = _read(tmp_path, "mvc/controllers/article_controller.py")
    model = _read(tmp_path, "mvc/models/article_model.py")
    index_html = _read(tmp_path, "mvc/views/article/_table.html")
    show_html = _read(tmp_path, "mvc/views/article/show.html")

    assert "get_article_tag_labels_by_article_id" in controller
    assert "[row[\"Id\"] for row in articles]" in controller
    assert '"tags_by_article_id": get_article_tag_labels_by_article_id' in controller
    assert "def get_article_tag_labels_by_article_id(ids):" in model
    assert "grouped.setdefault(row[\"source_id\"], []).append(row[\"target_label\"])" in model
    assert "SELECT pivot.article_id AS source_id" in model
    assert "FROM article_tag pivot" in model
    assert "JOIN tag ON tag.Id = pivot.tag_id" in model
    assert "WHERE pivot.article_id IN (" in model
    assert "Tag</th>" in index_html
    assert "tags_by_article_id.get(article.Id, [])" in index_html
    assert '| join(", ") if _tag_ids_labels else "—"' in index_html
    assert "get_article_tag_labels(id)" in controller
    assert '"tag_labels": tag_labels' in controller
    assert "def get_article_tag_labels(id):" in model
    assert "WHERE pivot.article_id = ?" in model
    assert "tag_labels | join(\", \")" in show_html
    assert "Aucun Tag" in show_html


def test_plusieurs_relations_many_to_many_generent_plusieurs_affichages(tmp_path):
    _run_article(
        tmp_path,
        relations=_relations(
            _canonical_m2m("Article", "Category", "categories", "article_category", "article_id", "category_id")
        ),
    )

    controller = _read(tmp_path, "mvc/controllers/article_controller.py")
    index_html = _read(tmp_path, "mvc/views/article/_table.html")
    show_html = _read(tmp_path, "mvc/views/article/show.html")

    assert "tags_by_article_id" in controller
    assert "categorys_by_article_id" in controller
    assert "tags_by_article_id.get(article.Id, [])" in index_html
    assert "categorys_by_article_id.get(article.Id, [])" in index_html
    assert "tag_labels | join" in show_html
    assert "category_labels | join" in show_html


def test_formulaires_et_sync_many_to_many_restent_inchanges(tmp_path):
    _run_article(tmp_path)

    form_html = _read(tmp_path, "mvc/views/article/form.html")
    model = _read(tmp_path, "mvc/models/article_model.py")
    controller = _read(tmp_path, "mvc/controllers/article_controller.py")

    assert 'name="tag_ids"' in form_html
    assert "{% for value, label in tag_choices %}" in form_html
    assert "tag_ids_selected" in form_html
    assert "def add_article_tag_ids(id, selected_ids):" in model
    assert "def sync_article_tag_ids(id, selected_ids):" in model
    assert "add_article_tag_ids(created_id, tag_ids)" in controller
    assert "sync_article_tag_ids(id, tag_ids)" in controller


def test_pas_de_repository_pivot_ni_modification_auth_rbac(tmp_path):
    _run_article(tmp_path)

    generated = "\n".join(
        [
            _read(tmp_path, "mvc/models/article_model.py"),
            _read(tmp_path, "mvc/controllers/article_controller.py"),
            _read(tmp_path, "mvc/views/article/form.html"),
        ]
    )

    assert "repository" not in generated.lower()
    assert "attach_" not in generated
    assert "auth" not in generated.lower()
    assert "require_user_permission" not in generated
