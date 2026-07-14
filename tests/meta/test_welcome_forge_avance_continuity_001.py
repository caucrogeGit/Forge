"""Garde-fou WELCOME-FORGE-LEVELS-ADR-028 : continuité du niveau avancé.

Depuis ADR-028, le niveau avancé welcome-forge est un **tutoriel continu
manuel** : un mini-projet « Catalogue d'articles » qui grandit palier après
palier, plus aucun starter buildable. Ce garde-fou verrouille :

- les paliers existent dans l'ordre pédagogique ;
- aucune page ne propose `forge starter:build` (parcours manuel) ;
- chaque palier montre l'état cumulatif de `mvc/routes.py` (groupe public, route
  `articles_index`), et les routes apparaissent dès qu'elles sont introduites ;
- le dernier palier (`json-api`) pointe vers le bilan du niveau ;
- le bilan présente l'état final (ArticleController complet + routes) ;
- style francophone : aucun tiret cadratin U+2014 ;
- les blocs Python des pages sont du Python valide.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
AVANCE = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "avance"

# Ordre pédagogique du mini-projet Catalogue d'articles.
# ADR-042 : le palier upload (qui utilisait l'opt-in forge-mvc-files) a été
# retiré du parcours cœur ; le mini-projet enchaîne relations -> transaction -> API JSON.
PALIERS = ["relations", "db-transaction", "json-api"]

CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _read(slug: str) -> str:
    return (AVANCE / f"{slug}.md").read_text(encoding="utf-8")


def _parses(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        try:
            ast.parse("class _W:\n" + "\n".join("    " + l for l in src.splitlines()))
            return True
        except SyntaxError:
            return False


class TestPagesExist:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_page_exists(self, slug):
        assert (AVANCE / f"{slug}.md").exists(), (
            f"La page {slug}.md du niveau avancé doit exister."
        )


class TestStyleFrancophone:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_no_em_dash(self, slug):
        assert "—" not in _read(slug), (
            f"{slug}.md contient un tiret cadratin U+2014 (interdit, "
            "style francophone CLAUDE.md §2.1)."
        )


class TestParcoursManuel:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_no_starter_build(self, slug):
        assert "forge starter:build" not in _read(slug), (
            f"{slug}.md ne doit pas proposer `forge starter:build` "
            "(tutoriel continu manuel, ADR-028)."
        )


class TestContinuiteCumulative:

    @pytest.mark.parametrize("slug", PALIERS)
    def test_etat_cumulatif_routes(self, slug):
        content = _read(slug)
        assert 'router.group("", public=True)' in content, (
            f"{slug}.md doit montrer le groupe public cumulatif de mvc/routes.py."
        )
        assert "ArticleController.index" in content, (
            f"{slug}.md doit inclure la route de base `articles_index` (cumulatif)."
        )

    @pytest.mark.parametrize("slug", ["db-transaction", "json-api"])
    def test_routes_creation_presentes_des_palier_2(self, slug):
        assert "ArticleController.store" in _read(slug), (
            f"{slug}.md doit conserver la route de création (cumulatif)."
        )

    def test_api_route_presente_au_dernier_palier(self):
        assert "ArticleController.api_index" in _read("json-api"), (
            "json-api.md doit déclarer la route api_articles."
        )

    def test_chaine_des_paliers(self):
        for src, nxt in zip(PALIERS, PALIERS[1:]):
            assert f"({nxt}.md)" in _read(src), f"{src}.md doit pointer vers {nxt}.md."
        assert "(bilan.md)" in _read(PALIERS[-1]), (
            "json-api.md doit pointer vers bilan.md."
        )


class TestEtatFinalDansBilan:
    MARKERS = [
        "class ArticleController",
        "def index", "def create", "def store", "def api_index",
        "article-index", "article-store", "article-api_index",
    ]

    @pytest.mark.parametrize("marker", MARKERS)
    def test_bilan_montre_etat_final(self, marker):
        assert marker in _read("bilan"), (
            f"Le bilan avancé doit montrer l'état final (`{marker}`)."
        )


class TestBlocsPythonValides:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_python_blocks_parse(self, slug):
        for block in CODE_BLOCK.findall(_read(slug)):
            assert _parses(block.rstrip("\n")), (
                f"{slug}.md contient un bloc Python invalide."
            )
