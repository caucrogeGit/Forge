"""Garde-fous ADR-073 — namespace app/ des vues applicatives (retour terrain 018 F41).

Vérifie que `make:crud` :
- range les vues sous `mvc/views/<ns>/<snake>/` quand un namespace est donné,
  et que les `render(...)` / `{% include %}` générés portent le même préfixe ;
- reste à plat (`mvc/views/<snake>/`) quand le namespace est vide (rétro-compat) ;
- ne namespace JAMAIS les URLs de routes (`/<snake>/...` inchangées) ;
et que le défaut du générateur coïncide avec celui du squelette (config.py).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_entities")

from forge_mvc_entities.crud.views_namespace import (
    DEFAULT_APP_VIEWS_NAMESPACE,
    entity_view_dir,
    resolve_app_views_namespace,
)
from forge_mvc_entities.crud.utils import _to_snake
from forge_mvc_entities.make_crud import make_crud

_CONTACT = {
    "schema_version": "1.0",
    "name": "Contact",
    "table": "contact",
    "description": "",
    "fields": [
        {"name": "nom", "type": "string", "max_length": 100, "required": True},
        {"name": "email", "type": "string", "nullable": True},
    ],
}


def _generate(tmp_path: Path, views_namespace: str) -> Path:
    snake = _to_snake(_CONTACT["name"])
    entity_dir = tmp_path / "mvc" / "entities" / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(_CONTACT), encoding="utf-8")
    make_crud(
        _CONTACT["name"],
        entities_root=tmp_path / "mvc" / "entities",
        output_root=tmp_path,
        views_namespace=views_namespace,
    )
    return tmp_path


def _read(root: Path, rel: str) -> str:
    return (root / rel).read_text(encoding="utf-8")


# ── Helpers purs ──────────────────────────────────────────────────────────────

def test_entity_view_dir():
    assert entity_view_dir("eleve", "app") == "app/eleve"
    assert entity_view_dir("eleve", "") == "eleve"
    assert entity_view_dir("eleve", "/app/") == "app/eleve"  # slashes de bord tolérés


def test_default_namespace_is_app():
    assert DEFAULT_APP_VIEWS_NAMESPACE == "app"


def test_generator_default_matches_skeleton_config():
    """Le défaut du générateur coïncide avec celui du squelette (config.py)."""
    config_src = (
        Path(__file__).resolve().parents[1] / "skeleton" / "data" / "config.py"
    ).read_text(encoding="utf-8")
    assert f'APP_VIEWS_NAMESPACE = os.getenv("APP_VIEWS_NAMESPACE", "{DEFAULT_APP_VIEWS_NAMESPACE}")' in config_src


# ── Résolution tolérante ──────────────────────────────────────────────────────

def test_resolve_defaults_to_app_without_project(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # aucun config.py
    assert resolve_app_views_namespace() == "app"


def test_resolve_reads_config_value(tmp_path, monkeypatch):
    (tmp_path / "config.py").write_text('APP_VIEWS_NAMESPACE = "zone"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert resolve_app_views_namespace() == "zone"


def test_resolve_empty_stays_flat(tmp_path, monkeypatch):
    (tmp_path / "config.py").write_text('APP_VIEWS_NAMESPACE = ""\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert resolve_app_views_namespace() == ""


# ── Génération namespacée ─────────────────────────────────────────────────────

def test_views_written_under_namespace(tmp_path):
    root = _generate(tmp_path, "app")
    for leaf in ("index.html", "_table.html", "_pagination.html",
                 "_results.html", "show.html", "form.html"):
        assert (root / "mvc" / "views" / "app" / "contact" / leaf).is_file(), leaf
    # Rien à la racine plate.
    assert not (root / "mvc" / "views" / "contact").exists()


def test_controller_render_calls_use_namespace(tmp_path):
    root = _generate(tmp_path, "app")
    ctrl = _read(root, "mvc/controllers/contact_controller.py")
    assert 'render("app/contact/index.html"' in ctrl or 'template = "app/contact/' in ctrl
    assert 'render("app/contact/show.html"' in ctrl
    assert 'render("app/contact/form.html"' in ctrl
    # Aucun render vers le chemin plat.
    assert 'render("contact/' not in ctrl


def test_includes_use_namespace(tmp_path):
    root = _generate(tmp_path, "app")
    index_html = _read(root, "mvc/views/app/contact/index.html")
    results = _read(root, "mvc/views/app/contact/_results.html")
    assert '{% include "app/contact/_results.html" %}' in index_html
    assert '{% include "app/contact/_table.html" %}' in results
    assert '{% include "app/contact/_pagination.html" %}' in results


def test_routes_are_not_namespaced(tmp_path):
    """Le namespace concerne les VUES, jamais les URLs de routes."""
    root = _generate(tmp_path, "app")
    ctrl = _read(root, "mvc/controllers/contact_controller.py")
    assert '"/contact/create"' in ctrl
    assert '"/app/contact/' not in ctrl  # aucune URL polluée par le namespace


# ── Rétro-compatibilité (namespace vide = plat) ───────────────────────────────

def test_empty_namespace_stays_flat(tmp_path):
    root = _generate(tmp_path, "")
    assert (root / "mvc" / "views" / "contact" / "index.html").is_file()
    assert not (root / "mvc" / "views" / "app").exists()
    ctrl = _read(root, "mvc/controllers/contact_controller.py")
    assert 'render("contact/show.html"' in ctrl
    index_html = _read(root, "mvc/views/contact/index.html")
    assert '{% include "contact/_results.html" %}' in index_html
