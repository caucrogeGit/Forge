"""Garde-fou LANDING-SEARCH-BAR-001.

Vérifie que :
1. Le plugin search est activé dans mkdocs.yml.
2. La barre de recherche est présente dans la landing source et générée.
3. Elle redirige vers la page de recherche mkdocs avec le paramètre q.
4. Elle a un label d'accessibilité.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING_SOURCE = PROJECT_ROOT / "docs" / "index.html"
LANDING_GENERATED = PROJECT_ROOT / "docs" / "index.html"


class TestSearchPluginEnabled:

    def test_search_plugin_declared(self):
        text = (PROJECT_ROOT / "mkdocs.yml").read_text(encoding="utf-8")
        has_search = bool(re.search(r"^\s*-\s*search", text, re.MULTILINE)) or "search:" in text
        assert has_search, (
            "Le plugin 'search' doit être activé dans mkdocs.yml.\n"
            "Ajouter :\nplugins:\n  - search"
        )


class TestSearchBarInLanding:

    def test_search_bar_in_source(self):
        text = LANDING_SOURCE.read_text(encoding="utf-8")
        assert 'name="q"' in text, (
            f"{LANDING_SOURCE} doit contenir un <input name=\"q\"> pour la recherche."
        )

    def test_search_form_action_in_source(self):
        text = LANDING_SOURCE.read_text(encoding="utf-8")
        assert 'action="/search/"' in text or 'action="search/"' in text, (
            f"{LANDING_SOURCE} doit avoir <form action=\"search/\"> ou "
            f"<form action=\"/search/\"> pour rediriger vers mkdocs search."
        )

    def test_search_bar_in_generated(self):
        text = LANDING_GENERATED.read_text(encoding="utf-8")
        assert 'name="q"' in text, (
            f"{LANDING_GENERATED} doit contenir la barre de recherche. "
            f"Régénérer via : forge sync:landing"
        )


class TestSearchBarAccessibility:

    def test_has_aria_label(self):
        text = LANDING_SOURCE.read_text(encoding="utf-8")
        assert 'aria-label="Rechercher' in text or 'aria-label="Lancer la recherche"' in text, (
            "La barre de recherche doit avoir un aria-label pour l'accessibilité."
        )

    def test_has_role_search(self):
        text = LANDING_SOURCE.read_text(encoding="utf-8")
        assert 'role="search"' in text, (
            "Le formulaire de recherche doit avoir role=\"search\" pour l'accessibilité."
        )
