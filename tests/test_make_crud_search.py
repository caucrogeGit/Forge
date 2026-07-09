"""Tests de la recherche simple generee par forge make:crud."""

import json
from pathlib import Path

from forge_mvc_entities.make_crud import (
    build_controller,
    build_form_view,
    build_index_view,
    build_model,
    build_pagination_partial,
    build_show_view,
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
        "constraints": {},
        "unique": False,
    }


ARTICLE = {
    "entity": "Article",
    "table": "article",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("titre", "VARCHAR(150)", python_type="str"),
        _field("description", "TEXT", python_type="str", nullable=True),
        _field("vues", "INT", python_type="int"),
        _field("publie", "BOOLEAN", python_type="bool"),
        _field("cree_le", "DATE", python_type="date"),
    ],
}

SCORE = {
    "entity": "Score",
    "table": "score",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("valeur", "INT", python_type="int"),
    ],
}

AUTHOR = {
    "entity": "Auteur",
    "table": "auteur",
    "description": "",
    "fields": [
        _field("code", "VARCHAR(20)", python_type="str", primary_key=True),
        _field("nom", "VARCHAR(100)", python_type="str"),
    ],
}

ARTICLE_WITH_TEXT_FK = {
    "entity": "Article",
    "table": "article",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("titre", "VARCHAR(150)", python_type="str"),
        _field("auteur_code", "VARCHAR(20)", python_type="str"),
    ],
}

TAG = {
    "entity": "Tag",
    "table": "tag",
    "description": "",
    "fields": [
        _field("id", "INT", python_type="int", primary_key=True, auto_increment=True),
        _field("nom", "VARCHAR(80)", python_type="str"),
    ],
}


def _write_entity(root: Path, definition: dict) -> None:
    snake = definition["entity"].lower()
    entity_dir = root / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


def _entities_root(tmp_path: Path, *definitions: dict, relations: dict | None = None) -> Path:
    root = tmp_path / "mvc" / "entities"
    for definition in definitions:
        _write_entity(root, definition)
    if relations is not None:
        root.mkdir(parents=True, exist_ok=True)
        (root / "relations.json").write_text(json.dumps(relations), encoding="utf-8")
    return root


def _search_cols_line(code: str) -> str:
    return next(line for line in code.splitlines() if line.startswith("_SEARCH_COLS"))


def test_make_crud_genere_champ_get_q_dans_index():
    html = build_index_view(ARTICLE)

    assert '<form method="get"' in html
    assert 'type="search"' in html
    assert 'name="q"' in html
    assert 'value="{{ pagination.q }}"' in html
    assert 'hx-get="/article"' in html
    assert "<script" not in html


def test_controller_lit_q_depuis_la_requete_et_strip():
    code = build_controller(ARTICLE)

    assert 'q         = _query_param(request, "q").strip()' in code
    assert "request.params.get(name, [default])" in code
    assert "request.query" not in code
    assert "q=q or None" in code
    assert '"q": q' in code


def test_q_vide_ne_declenche_pas_de_recherche_active():
    code = build_model(ARTICLE)

    assert "if q and _SEARCH_COLS:" in code
    assert 'clauses.append("(" + " OR ".join(c + " LIKE ?" for c in _SEARCH_COLS) + ")")' in code


def test_q_non_vide_utilise_like_parametre_sur_champs_texte():
    code = build_model(ARTICLE)
    search_line = _search_cols_line(code)

    assert "Titre" in search_line
    assert "Description" in search_line
    assert "Vues" not in search_line
    assert "Publie" not in search_line
    assert "CreeLe" not in search_line
    assert "Id" not in search_line
    assert "LIKE ?" in code
    assert 'params.extend("%" + q + "%" for _ in _SEARCH_COLS)' in code
    assert "LIKE '%" not in code
    assert '"%" + q + "%"' in code


def test_entite_sans_champ_texte_garde_recherche_inactive():
    code = build_model(SCORE)

    assert "_SEARCH_COLS  = []" in code
    assert "if q and _SEARCH_COLS:" in code


def test_fk_many_to_one_textuelle_est_exclue_des_champs_recherchables(tmp_path):
    relations = {
        "schema_version": "1.0",
        "relations": [
            {
                "name": "article_auteur",
                "type": "many_to_one",
                "from": "Article",
                "to": "Auteur",
                "foreign_key": "auteur_code",
                "on_delete": "restrict",
            }
        ],
    }
    root = _entities_root(tmp_path, ARTICLE_WITH_TEXT_FK, AUTHOR, relations=relations)

    make_crud("Article", entities_root=root, output_root=tmp_path)
    code = (tmp_path / "mvc" / "models" / "article_model.py").read_text(encoding="utf-8")
    search_line = _search_cols_line(code)

    assert "article.Titre" in search_line
    assert "article.AuteurCode" not in search_line


def test_pagination_conserve_q_dans_les_liens():
    html = build_pagination_partial(ARTICLE)

    assert "{% if pagination.q %}&amp;q={{ pagination.q | urlencode }}{% endif %}" in html
    assert "page={{ pagination.page - 1 }}" in html
    assert "page={{ pagination.page + 1 }}" in html


def test_recherche_compatible_avec_many_to_many_source(tmp_path):
    relations = {
        "schema_version": "1.0",
        "relations": [
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
            }
        ],
    }
    root = _entities_root(tmp_path, ARTICLE, TAG, relations=relations)

    make_crud("Article", entities_root=root, output_root=tmp_path)
    controller = (tmp_path / "mvc" / "controllers" / "article_controller.py").read_text(encoding="utf-8")
    index = (tmp_path / "mvc" / "views" / "article" / "index.html").read_text(encoding="utf-8")
    table = (tmp_path / "mvc" / "views" / "article" / "_table.html").read_text(encoding="utf-8")

    assert 'q         = _query_param(request, "q").strip()' in controller
    assert "tags_by_article_id" in controller
    assert 'type="search"' in index
    assert "tags_by_article_id" in table


def test_recherche_ne_modifie_pas_show_ni_formulaires():
    show_html = build_show_view(ARTICLE)
    form_html = build_form_view(ARTICLE)
    controller = build_controller(ARTICLE)

    assert "def show(request: Request) -> Response:" in controller
    assert "def new(request: Request) -> Response:" in controller
    assert "def create(request: Request) -> Response:" in controller
    assert "def edit(request: Request) -> Response:" in controller
    assert "def update(request: Request) -> Response:" in controller
    assert "def destroy(request: Request) -> Response:" in controller
    assert 'type="search"' not in show_html
    assert 'type="search"' not in form_html
