"""Garde-fou STARTER-WELCOME-FORGE-TESTS-PIVOT-001 : continuité du tutoriel.

Depuis ADR-025, le niveau débutant welcome-forge est un **tutoriel continu
manuel** (un projet qui grandit, pas des starters indépendants). Ce test
verrouille la continuité documentaire des 11 paliers :

- chaque page palier montre l'état cumulatif de `mvc/routes.py`, incluant la
  route du palier courant ET celle du palier précédent (preuve de croissance) ;
- la page `bilan.md` présente l'état final complet (les 11 notions + les deux
  contrôleurs) ;
- aucune page ne propose `forge starter:build` (parcours manuel) ;
- style francophone : aucun tiret cadratin U+2014 ;
- les blocs Python des pages sont du Python valide.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
DEBUTANT = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "debutant"

PALIERS = [
    "welcome", "query-params", "first-html-view", "dynamic-route",
    "request-debug", "json-response", "csrf", "form-post",
    "server-validation", "first-sql", "first-sql-write",
]

# Route emblématique attendue dans le bloc cumulatif de chaque palier.
ROUTE_NAME = {
    "welcome": "welcome_index",
    "query-params": "query_params_hello",
    "first-html-view": "first_html_view_index",
    "dynamic-route": "dynamic_route_article_show",
    "request-debug": "request_debug_index",
    "json-response": "json_response_index",
    "csrf": "csrf_index",
    "form-post": "form_post_submit",
    "server-validation": "server_validation_submit",
    "first-sql": "first_sql_index",
    "first-sql-write": "first_sql_write_submit",
}

CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _read(slug: str) -> str:
    return (DEBUTANT / f"{slug}.md").read_text(encoding="utf-8")


def _all_pages() -> list[Path]:
    return sorted(DEBUTANT.glob("*.md"))


def _parses(src: str) -> bool:
    try:
        ast.parse(src)
        return True
    except SyntaxError:
        return False


class TestPagesExist:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_page_exists(self, slug):
        assert (DEBUTANT / f"{slug}.md").exists(), (
            f"La page {slug}.md du parcours débutant doit exister."
        )


class TestStyleFrancophone:
    @pytest.mark.parametrize("page", _all_pages(), ids=lambda p: p.name)
    def test_no_em_dash(self, page):
        assert "—" not in page.read_text(encoding="utf-8"), (
            f"{page.name} contient un tiret cadratin U+2014 (interdit, "
            "style francophone CLAUDE.md §2.1)."
        )


class TestParcoursManuel:
    @pytest.mark.parametrize("page", _all_pages(), ids=lambda p: p.name)
    def test_no_starter_build(self, page):
        assert "forge starter:build" not in page.read_text(encoding="utf-8"), (
            f"{page.name} ne doit pas proposer `forge starter:build` "
            "(tutoriel continu manuel, ADR-025)."
        )


class TestContinuiteCumulative:

    @pytest.mark.parametrize("slug", PALIERS)
    def test_route_du_palier_presente(self, slug):
        assert ROUTE_NAME[slug] in _read(slug), (
            f"{slug}.md doit montrer la route `{ROUTE_NAME[slug]}`."
        )

    @pytest.mark.parametrize("idx", range(1, len(PALIERS)))
    def test_etat_cumulatif_inclut_le_precedent(self, idx):
        slug = PALIERS[idx]
        prev = PALIERS[idx - 1]
        content = _read(slug)
        assert ROUTE_NAME[prev] in content, (
            f"{slug}.md doit rappeler l'état cumulatif en incluant la route "
            f"du palier précédent (`{ROUTE_NAME[prev]}`)."
        )

    @pytest.mark.parametrize("slug", PALIERS)
    def test_bloc_groupe_cumulatif(self, slug):
        assert 'router.group("", public=True)' in _read(slug), (
            f"{slug}.md doit montrer le groupe public cumulatif "
            '`with router.group("", public=True) as pub:`.'
        )


class TestEtatFinalDansBilan:

    NOTIONS = [
        'Response.text("Bonjour Forge")',
        'request.query("name"',
        "BaseController.render(",
        'request.route("id"',
        "Response.debug(request.data)",
        "Response.json(",
        "BaseController.csrf_token(request)",
        'request.form("name"',
        "status=422",
        "fetch_one(",
        "insert(",
    ]

    @pytest.mark.parametrize("notion", NOTIONS)
    def test_bilan_contient_notion(self, notion):
        assert notion in _read("bilan"), (
            f"bilan.md doit présenter l'état final contenant « {notion} »."
        )

    def test_bilan_montre_les_deux_controleurs(self):
        content = _read("bilan")
        assert "class WelcomeController" in content, (
            "bilan.md doit montrer la classe finale WelcomeController."
        )
        assert "class MessageController" in content, (
            "bilan.md doit montrer la classe finale MessageController."
        )


class TestBlocsPythonValides:
    @pytest.mark.parametrize("page", _all_pages(), ids=lambda p: p.name)
    def test_blocs_parsent(self, page):
        text = page.read_text(encoding="utf-8")
        for i, block in enumerate(CODE_BLOCK.findall(text)):
            if _parses(block):
                continue
            # Fragment de méthode(s) ou de ligne(s) indentée(s) : on l'enveloppe
            # dans une classe factice pour valider la syntaxe.
            if _parses("class _Tmp:\n" + block):
                continue
            pytest.fail(
                f"{page.name} : bloc Python #{i} invalide.\n---\n{block}\n---"
            )
