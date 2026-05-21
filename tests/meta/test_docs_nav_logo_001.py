"""Garde-fou DOCS-NAV-LOGO-SIZE-001.

Contrat : le logo MkDocs est agrandi via CSS dédié.
- docs/stylesheets/extra.css existe et contient le sélecteur md-header__button.md-logo ;
- la hauteur déclarée est 8rem ;
- mkdocs.yml référence extra_css: [stylesheets/extra.css] ;
- le logo forge-logo.png est présent dans docs/static/ ;
- le libellé texte Forge est masqué dans le header.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSS_FILE = PROJECT_ROOT / "docs" / "stylesheets" / "extra.css"
MKDOCS_YML = PROJECT_ROOT / "mkdocs.yml"


class TestDocsNavLogoCSS:
    """Le fichier CSS dédié au logo MkDocs est présent et correct."""

    def test_stylesheets_dir_existe(self):
        assert (PROJECT_ROOT / "docs" / "stylesheets").is_dir()

    def test_extra_css_existe(self):
        assert CSS_FILE.exists(), "docs/stylesheets/extra.css doit exister"

    def test_selecteur_md_logo_present(self):
        content = CSS_FILE.read_text(encoding="utf-8")
        assert ".md-header__button.md-logo" in content, (
            "extra.css doit cibler .md-header__button.md-logo"
        )

    def test_hauteur_8rem_declaree(self):
        content = CSS_FILE.read_text(encoding="utf-8")
        assert "height: 8rem" in content, (
            "extra.css doit déclarer height: 8rem pour le logo"
        )

    def test_header_hauteur_adaptee(self):
        content = CSS_FILE.read_text(encoding="utf-8")
        assert ".md-header" in content, (
            "extra.css doit adapter la hauteur de .md-header"
        )

    def test_masquage_texte_forge_present(self):
        content = CSS_FILE.read_text(encoding="utf-8")
        assert ".md-header__title" in content, (
            "extra.css doit masquer le libellé texte Forge dans le header"
        )

    def test_display_none_present(self):
        content = CSS_FILE.read_text(encoding="utf-8")
        assert "display: none" in content, (
            "extra.css doit utiliser display: none pour masquer le texte redondant"
        )


class TestDocsNavLogoMkdocsYml:
    """mkdocs.yml référence correctement la feuille de style extra."""

    def test_extra_css_dans_mkdocs(self):
        content = MKDOCS_YML.read_text(encoding="utf-8")
        assert "extra_css" in content, (
            "mkdocs.yml doit déclarer extra_css"
        )

    def test_extra_css_pointe_vers_stylesheets(self):
        content = MKDOCS_YML.read_text(encoding="utf-8")
        assert "stylesheets/extra.css" in content, (
            "mkdocs.yml doit référencer stylesheets/extra.css"
        )

    def test_logo_forge_declare_dans_mkdocs(self):
        content = MKDOCS_YML.read_text(encoding="utf-8")
        assert "forge-logo.png" in content, (
            "mkdocs.yml doit déclarer forge-logo.png comme logo du thème"
        )


class TestDocsNavLogoAsset:
    """Le fichier logo est présent dans docs/static/."""

    def test_logo_present_dans_docs_static(self):
        assert (PROJECT_ROOT / "docs" / "static" / "forge-logo.png").exists(), (
            "docs/static/forge-logo.png doit exister"
        )
