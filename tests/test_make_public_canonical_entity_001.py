"""Garde-fou PUBLIC-CANONICAL-ENTITY-001.

make:entity écrit les fichiers d'entités au format canonique
(`schema_version: "1.0"`, types Forge abstraits). Avant ce ticket, les
générateurs make:public-list/show/form passaient ce JSON canonique
directement au validateur legacy V1 (`validate_entity_definition`) sans le
pont de normalisation canonique -> forme interne. Résultat : ils échouaient
sur toute entité réelle, alors que les tests restaient verts car leurs
fixtures utilisaient l'ancienne forme interne (`sql_type`/`column`/...).

Ces tests reproduisent le cas réel : une entité canonique, et vérifient que
les trois générateurs la chargent et produisent leur scaffolding.
"""
from __future__ import annotations

import json
from pathlib import Path

from cli.public.public_form import make_public_form
from cli.public.public_list import (
    load_public_list_definition,
    make_public_list,
    make_public_show,
    public_list_fields,
)

# Entité canonique équivalente à ce que make:entity produit (aucune clé
# legacy sql_type/column/primary_key ; types Forge abstraits).
CANONICAL_ARTICLE = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "label": "Article",
    "plural_label": "Articles",
    "description": "Article canonique de test PUBLIC-CANONICAL-ENTITY-001.",
    "fields": [
        {"name": "title", "type": "string", "max_length": 255, "required": True},
        {"name": "content", "type": "text", "nullable": True},
        {"name": "published", "type": "boolean", "default": False},
        {"name": "published_at", "type": "datetime", "nullable": True},
    ],
    "options": {"timestamps": True, "soft_delete": False},
}


def _prepare_canonical_project(root: Path) -> None:
    entity_dir = root / "mvc" / "entities" / "article"
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / "article.json").write_text(
        json.dumps(CANONICAL_ARTICLE), encoding="utf-8"
    )
    (root / "mvc" / "views" / "layouts").mkdir(parents=True, exist_ok=True)
    (root / "mvc" / "views" / "layouts" / "public.html").write_text(
        "{% block title %}Forge{% endblock %}\n"
        "{% block content %}{% endblock %}\n"
        "{% block scripts %}{% endblock %}\n",
        encoding="utf-8",
    )
    routes_dir = root / "mvc" / "routes"
    routes_dir.mkdir(parents=True, exist_ok=True)
    (routes_dir / "__init__.py").write_text(
        "from core.http.router import Router\n\nrouter = Router()\n",
        encoding="utf-8",
    )


def _read(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def test_load_public_list_definition_accepte_le_canonique(tmp_path):
    """Le loader ne lève plus sur une entité canonique (le bug d'origine)."""
    _prepare_canonical_project(tmp_path)

    definition = load_public_list_definition(
        "Article", entities_root=tmp_path / "mvc" / "entities"
    )

    assert definition["entity"] == "Article"
    assert definition["table"] == "articles"


def test_public_list_fields_canonique_exclut_les_horodatages(tmp_path):
    _prepare_canonical_project(tmp_path)

    definition = load_public_list_definition(
        "Article", entities_root=tmp_path / "mvc" / "entities"
    )
    names = [field.name for field in public_list_fields(definition)]

    assert names == ["title", "content", "published", "published_at"]
    assert "created_at" not in names
    assert "updated_at" not in names
    assert "id" not in names


def test_make_public_list_sur_entite_canonique(tmp_path):
    _prepare_canonical_project(tmp_path)

    make_public_list("Article", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_articles_controller.py")
    assert "class PublicArticlesController(BaseController):" in controller
    assert "def index(request: Request) -> Response:" in controller
    assert "FROM articles" in controller
    template = _read(tmp_path, "mvc/views/public/articles/index.html")
    assert "{% for row in articles %}" in template


def test_make_public_show_sur_entite_canonique(tmp_path):
    _prepare_canonical_project(tmp_path)

    make_public_show("Article", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_articles_controller.py")
    assert "def show(request: Request) -> Response:" in controller
    assert "FROM articles WHERE" in controller
    template = _read(tmp_path, "mvc/views/public/articles/show.html")
    assert "{% block content %}" in template


def test_make_public_form_sur_entite_canonique(tmp_path):
    _prepare_canonical_project(tmp_path)

    make_public_form("Article", output_root=tmp_path)

    controller = _read(tmp_path, "mvc/controllers/public_articles_controller.py")
    assert "INSERT INTO articles" in controller
