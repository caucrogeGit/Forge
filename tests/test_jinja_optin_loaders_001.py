"""Garde-fou CORE-JINJA-OPTIN-LOADERS-001 (ADR-046).

Le renderer Jinja compose le dossier `mvc/views/` du projet avec les loaders de
templates contribués par les opt-ins (registre push du cœur). Propriétés
vérifiées :

- un opt-in peut faire rendre un template qu'il embarque ;
- le projet l'emporte sur le paquet (surcharge native par l'ordre des loaders) ;
- l'ordre d'import n'a pas d'importance (le registre est relu à la résolution),
  car le renderer du squelette est construit avant l'import des opt-ins ;
- un template introuvable lève toujours l'erreur Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import DictLoader

from core.mvc.controller import registry
from core.templating.errors import TemplateNotFoundError
from integrations.jinja2.renderer import Jinja2Renderer


@pytest.fixture(autouse=True)
def _isolate_registry():
    """Isole les registres Jinja : restaure l'état réel après chaque test.

    Les loaders d'opt-in (ex. forge-mvc-admin) sont enregistrés à l'import et
    constituent un état de session ; on les sauvegarde puis on les restaure pour
    ne pas les perdre pour les tests suivants.
    """
    saved_providers = registry.iter_jinja_context_providers()
    saved_loaders = registry.iter_jinja_template_loaders()
    registry._clear_for_tests()
    registry._clear_template_loaders_for_tests()
    for provider in saved_providers:
        registry.register_jinja_context_provider(provider)
    yield
    registry._clear_for_tests()
    registry._clear_template_loaders_for_tests()
    for provider in saved_providers:
        registry.register_jinja_context_provider(provider)
    for loader in saved_loaders:
        registry.register_jinja_template_loader(loader)


def _views(tmp_path: Path) -> str:
    views = tmp_path / "views"
    views.mkdir()
    return str(views)


def test_loader_optin_rend_un_template_embarque(tmp_path: Path):
    registry.register_jinja_template_loader(DictLoader({"admin/x.html": "PAQUET {{ v }}"}))
    renderer = Jinja2Renderer(_views(tmp_path))
    assert renderer.render("admin/x.html", {"v": 1}) == "PAQUET 1"


def test_le_projet_surcharge_le_paquet(tmp_path: Path):
    views = _views(tmp_path)
    (Path(views) / "admin").mkdir()
    (Path(views) / "admin" / "x.html").write_text("PROJET", encoding="utf-8")
    registry.register_jinja_template_loader(DictLoader({"admin/x.html": "PAQUET"}))
    renderer = Jinja2Renderer(views)
    assert renderer.render("admin/x.html", {}) == "PROJET"


def test_ordre_import_indifferent(tmp_path: Path):
    # Renderer construit AVANT l'enregistrement du loader (ordre du squelette).
    renderer = Jinja2Renderer(_views(tmp_path))
    registry.register_jinja_template_loader(DictLoader({"admin/late.html": "TARDIF"}))
    assert renderer.render("admin/late.html", {}) == "TARDIF"


def test_template_introuvable_leve(tmp_path: Path):
    renderer = Jinja2Renderer(_views(tmp_path))
    with pytest.raises(TemplateNotFoundError):
        renderer.render("inexistant.html", {})
