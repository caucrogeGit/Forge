"""SKELETON-CHARTE-001 — page de référence de la charte graphique.

Le squelette livre `mvc/views/pages/charte.html`, une page servable qui montre le thème
« Accessible chaleureux » (palette, typographie, composants), câblée sur `/charte`.
Elle sert de référence visible ; les tokens s'éditent dans `static/src/input.css`.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

SKELETON = Path(__file__).resolve().parent.parent / "skeleton" / "data"
VIEWS = SKELETON / "mvc" / "views"


def test_charte_view_existe():
    assert (VIEWS / "pages" / "charte.html").is_file()


def test_charte_route_et_controleur_cables():
    routes = (SKELETON / "mvc" / "routes" / "__init__.py").read_text(encoding="utf-8")
    assert 'public.add("GET", "/charte", HomeController.charte' in routes
    controller = (SKELETON / "mvc" / "controllers" / "home_controller.py").read_text(encoding="utf-8")
    assert "def charte(" in controller
    assert 'render("pages/charte.html"' in controller


def test_charte_pointe_vers_input_css():
    # La page indique où éditer la charte (le fichier de tokens Tailwind).
    content = (VIEWS / "pages" / "charte.html").read_text(encoding="utf-8")
    assert "static/src/input.css" in content


def test_charte_se_rend_avec_base_et_composants():
    env = Environment(loader=FileSystemLoader(str(VIEWS)), undefined=StrictUndefined)
    env.globals.update(app_name="Demo")
    html = env.get_template("pages/charte.html").render(flash=None)
    # Étend base.html (footer) et exerce les composants.
    assert "<footer" in html
    assert "bg-forge" in html                       # palette
    assert 'name="exemple_email"' in html           # macro field
    assert "Première option" in html                # macro select_field
    for label in ("Palette", "Boutons", "Badges", "Alertes"):
        assert label in html, label


@pytest.mark.parametrize("token_class", ["bg-forge", "bg-ink", "bg-cream", "bg-surface"])
def test_charte_montre_les_tokens_principaux(token_class):
    content = (VIEWS / "pages" / "charte.html").read_text(encoding="utf-8")
    assert token_class in content
