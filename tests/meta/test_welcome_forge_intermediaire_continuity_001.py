"""Garde-fou WELCOME-FORGE-LEVELS-ADR-028 : continuité du niveau intermédiaire.

Depuis ADR-028, le niveau intermédiaire welcome-forge est un **tutoriel continu
manuel** : un mini-projet « Carnet de notes » qui grandit palier après palier,
plus aucun starter buildable. Ce garde-fou verrouille :

- les 8 paliers existent dans l'ordre pédagogique ;
- aucune page ne propose `forge starter:build` (parcours manuel) ;
- chaque palier montre l'état cumulatif de `mvc/routes.py` (groupe public,
  route `notes_index`), et les routes d'écriture apparaissent dès qu'elles sont
  introduites (preuve de croissance) ;
- le dernier palier (`session-state`) pointe vers le bilan du niveau ;
- le bilan présente l'état final (NoteController complet + routes) ;
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
INTER = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "intermediaire"

# Ordre pédagogique du mini-projet Carnet de notes.
PALIERS = [
    "list-records", "layout-template", "filter-list", "pagination",
    "update-record", "delete-record", "flash-messages", "session-state",
]

CODE_BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _read(slug: str) -> str:
    return (INTER / f"{slug}.md").read_text(encoding="utf-8")


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
        assert (INTER / f"{slug}.md").exists(), (
            f"La page {slug}.md du niveau intermédiaire doit exister."
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
        assert "NoteController.index" in content, (
            f"{slug}.md doit inclure la route de base `notes_index` (cumulatif)."
        )

    @pytest.mark.parametrize("slug", ["update-record", "delete-record",
                                      "flash-messages", "session-state"])
    def test_routes_edition_presentes_des_palier_5(self, slug):
        # notes_edit / notes_update introduites au palier 5, présentes ensuite.
        content = _read(slug)
        assert "NoteController.edit" in content and "NoteController.update" in content, (
            f"{slug}.md doit conserver les routes d'édition (croissance cumulative)."
        )

    @pytest.mark.parametrize("slug", ["delete-record", "flash-messages", "session-state"])
    def test_route_suppression_presente_des_palier_6(self, slug):
        assert "NoteController.delete" in _read(slug), (
            f"{slug}.md doit conserver la route de suppression (cumulatif)."
        )

    def test_chaine_des_paliers(self):
        for src, nxt in zip(PALIERS, PALIERS[1:]):
            assert f"({nxt}.md)" in _read(src), f"{src}.md doit pointer vers {nxt}.md."
        assert "(bilan.md)" in _read(PALIERS[-1]), (
            "session-state.md doit pointer vers bilan.md."
        )


class TestEtatFinalDansBilan:
    MARKERS = [
        "class NoteController",
        "def index", "def edit", "def update", "def delete",
        "notes_index", "notes_edit", "notes_update", "notes_delete",
    ]

    @pytest.mark.parametrize("marker", MARKERS)
    def test_bilan_montre_etat_final(self, marker):
        assert marker in _read("bilan"), (
            f"Le bilan intermédiaire doit montrer l'état final (`{marker}`)."
        )


class TestBlocsPythonValides:
    @pytest.mark.parametrize("slug", PALIERS + ["bilan"])
    def test_python_blocks_parse(self, slug):
        for block in CODE_BLOCK.findall(_read(slug)):
            src = block.rstrip("\n")
            assert _parses(src), f"{slug}.md contient un bloc Python invalide."
