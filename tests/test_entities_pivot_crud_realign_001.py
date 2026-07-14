"""Tests — ENTITIES-PIVOT-CRUD-REALIGN-001 : make:pivot-crud réaligné et rendu réel.

L'audit 2026-07 a montré que make:pivot-crud générait une fonctionnalité cassée
de bout en bout depuis l'absorption ADR-070 : templates écrits sous
mvc/templates/ (hors racine Jinja mvc/views/), héritage d'un layouts/app.html
inexistant, bug de braces f-string (`#{eleve_id}` au lieu de `{{ eleve_id }}`),
instructions pointant mvc/routes.py (pré-ADR-068). Aucun test ne rendait les
templates : le garde central de ce ticket est un rendu Jinja RÉEL.

Garde-fous :
  1. les templates générés se rendent réellement via Jinja (héritage
     layouts/base.html résolu, contexte réaliste) ;
  2. le bug de f-string est corrigé : l'index affiche `Article #<id>` ;
  3. le namespace ADR-073 est honoré (vues sous mvc/views/<ns>/pivot/...,
     chemins de render() du contrôleur alignés) ;
  4. plus aucune trace des anciennes conventions (mvc/templates,
     layouts/app.html, mvc/routes.py) dans les fichiers générés.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")
jinja2 = pytest.importorskip("jinja2")

from forge_mvc_entities.make_pivot_crud import make_pivot_crud

_RELATIONS = {
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
                "fields": [
                    {"name": "position", "type": "integer", "nullable": False},
                    {"name": "note", "type": "string", "max_length": 120, "nullable": True},
                ],
            },
        }
    ],
}


def _generate(tmp_path: Path, namespace: str = "app") -> Path:
    rel_path = tmp_path / "mvc" / "entities" / "relations.json"
    rel_path.parent.mkdir(parents=True, exist_ok=True)
    rel_path.write_text(json.dumps(_RELATIONS), encoding="utf-8")
    make_pivot_crud(
        "Article", "tags",
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
        views_namespace=namespace,
    )
    return tmp_path / "mvc" / "views"


def _jinja_env(views_root: Path) -> "jinja2.Environment":
    # Layout minimal du squelette : le rendu échoue si l'héritage ne résout pas.
    layouts = views_root / "layouts"
    layouts.mkdir(parents=True, exist_ok=True)
    (layouts / "base.html").write_text(
        "<!doctype html><body>{% block content %}{% endblock %}</body>",
        encoding="utf-8",
    )
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(views_root)),
        autoescape=True,
        undefined=jinja2.StrictUndefined,
    )


class _Row:
    def __init__(self, target_id: int, pivot_data: dict[str, str]) -> None:
        self.target_id = target_id
        self.pivot_data = pivot_data


class TestRealRendering:
    def test_index_se_rend_reellement(self, tmp_path):
        views_root = _generate(tmp_path)
        env = _jinja_env(views_root)
        html = env.get_template("app/pivot/article_tags/index.html").render(
            article_id=7,
            rows=[_Row(3, {"position": "1", "note": "lead"})],
            csrf_token="tok",
        )
        assert "Article #7" in html, (
            "le bug de braces f-string doit rester corrigé "
            "(l'en-tête affichait le littéral « #{article_id} »)"
        )
        assert "lead" in html
        assert "<!doctype html>" in html, "l'héritage layouts/base.html doit résoudre"

    def test_index_vide_se_rend(self, tmp_path):
        views_root = _generate(tmp_path)
        env = _jinja_env(views_root)
        html = env.get_template("app/pivot/article_tags/index.html").render(
            article_id=7, rows=[], csrf_token="tok",
        )
        assert "Aucune association." in html

    def test_form_ajout_et_edition_se_rendent(self, tmp_path):
        views_root = _generate(tmp_path)
        env = _jinja_env(views_root)
        form = env.get_template("app/pivot/article_tags/form.html")
        ajout = form.render(
            article_id=7, row=None, action="/articles/7/tags/add", error=None,
            csrf_token="tok",
        )
        assert 'name="tag_id"' in ajout
        edition = form.render(
            article_id=7,
            row=_Row(3, {"position": "2", "note": ""}),
            action="/articles/7/tags/3/edit",
            error=None,
            csrf_token="tok",
        )
        assert 'value="2"' in edition


class TestNamespaceAlignment:
    def test_vues_sous_le_namespace_et_render_aligne(self, tmp_path):
        _generate(tmp_path, namespace="app")
        index = tmp_path / "mvc" / "views" / "app" / "pivot" / "article_tags" / "index.html"
        assert index.exists()
        ctrl = tmp_path / "mvc" / "controllers" / "pivot" / "article_tags_pivot_controller.py"
        src = ctrl.read_text(encoding="utf-8")
        assert '_TEMPLATE_INDEX = "app/pivot/article_tags/index.html"' in src
        assert '_TEMPLATE_FORM  = "app/pivot/article_tags/form.html"' in src

    def test_namespace_plat(self, tmp_path):
        _generate(tmp_path, namespace="")
        index = tmp_path / "mvc" / "views" / "pivot" / "article_tags" / "index.html"
        assert index.exists()


class TestOldConventionsGone:
    def test_aucune_trace_des_anciennes_conventions(self, tmp_path):
        _generate(tmp_path)
        produced = [
            p for p in tmp_path.rglob("*")
            if p.is_file() and p.suffix in {".py", ".html"}
        ]
        assert produced, "la génération doit produire des fichiers"
        for path in produced:
            text = path.read_text(encoding="utf-8")
            assert "layouts/app.html" not in text, path
            assert "mvc/routes.py" not in text, path
        assert not (tmp_path / "mvc" / "templates").exists(), (
            "plus aucun fichier sous mvc/templates/ (racine Jinja = mvc/views/)"
        )
