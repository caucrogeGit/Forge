"""Tests documentaires — STARTER-SEQUENTIAL-NAV-001.

Verrouille la navigation pédagogique séquentielle entre pages de
starters. Chaque page pointe vers le palier suivant via un lien
``../<slug>/`` (ou ``../<slug>/index.md``) dans une section
« Après ce starter ». Le starter autonome Premier CRUD clôt la
chaîne et renvoie vers la vue d'ensemble.

Vérifie aussi :

- absence des commandes de création/installation interdites dans
  TOUTES les pages `docs/starters/*/index.md` (``forge starter:build``,
  ``forge new mon-projet``, ``cd mon-projet``,
  ``source .venv/bin/activate``) ;
- absence des étiquettes par numéro (Starter 7…14) dans les pages
  pédagogiques (welcome → first-sql). contact-simple peut garder
  son numéro historique « 1 » (pas dans la plage 7–14 protégée).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS_DOCS = PROJECT_ROOT / "docs" / "starters"

# Chaînage attendu de la progression pédagogique :
# chaque page (clé) doit pointer vers la suivante (valeur).
SEQUENTIAL_CHAIN: dict[str, str] = {
    "welcome": "query-params",
    "query-params": "first-html-view",
    "first-html-view": "dynamic-route",
    "dynamic-route": "request-debug",
    "request-debug": "json-response",
    "json-response": "csrf",
    "csrf": "form-post",
    "form-post": "server-validation",
    "server-validation": "first-sql",
    "first-sql": "first-sql-write",
    "first-sql-write": "premier-crud",
}

# Pages pédagogiques (paliers 1→11). premier-crud et contact-simple sont
# exclus : ce sont des starters autonomes (dossier propre), qui peuvent
# garder des étiquettes historiques ("Starter 1").
PEDAGOGICAL_PAGES = list(SEQUENTIAL_CHAIN.keys())

# Starters autonomes rendus dans leur propre dossier docs/starters/<slug>/.
STANDALONE_STARTERS = ["premier-crud", "contact-simple"]

# Toutes les pages starters concernées par la règle stricte
# d'absence des commandes de création.
ALL_STARTER_PAGES = PEDAGOGICAL_PAGES + STANDALONE_STARTERS

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _doc_path(slug: str) -> Path:
    # DOCS-STARTERS-PROGRESSION-FOLDER-001 — les paliers pédagogiques
    # (welcome → first-sql) sont regroupés à plat dans
    # docs/starters/welcome/<slug>.md. contact-simple garde son
    # dossier historique.
    if slug in STANDALONE_STARTERS:
        return STARTERS_DOCS / slug / "index.md"
    return STARTERS_DOCS / "welcome" / f"{slug}.md"


# ── Chaînage séquentiel : chaque page pointe vers la suivante ─────────────────


class TestSequentialChain:

    @pytest.mark.parametrize("source,target", list(SEQUENTIAL_CHAIN.items()))
    def test_page_points_to_next_palier(self, source: str, target: str):
        page = _doc_path(source)
        content = page.read_text(encoding="utf-8")
        # DOCS-STARTERS-PROGRESSION-FOLDER-001 — au sein de welcome/, le
        # palier suivant est un fichier frère « target.md » ; le dernier
        # palier (first-sql) pointe vers contact-simple resté dans son
        # dossier (« ../contact-simple/ »).
        if target in STANDALONE_STARTERS:
            link_variants = (f"../{target}/", f"../{target}/index.md")
        else:
            link_variants = (f"{target}.md", f"{target}/")
        assert any(v in content for v in link_variants), (
            f"{page} doit contenir un lien vers le palier suivant "
            f"« {link_variants[0]} » (STARTER-SEQUENTIAL-NAV-001)."
        )

    def test_last_palier_points_to_premier_crud(self):
        # Le dernier palier de la progression de découverte est
        # first-sql-write (écriture en base) ; sa section « Après ce
        # starter » pointe vers le premier starter autonome, premier-crud.
        content = _doc_path("first-sql-write").read_text(encoding="utf-8")
        assert "../premier-crud/" in content

    def test_premier_crud_returns_to_overview(self):
        # premier-crud clôt la chaîne pédagogique et renvoie vers ../
        content = _doc_path("premier-crud").read_text(encoding="utf-8")
        # On cherche un lien retour explicite vers la vue d'ensemble
        # des starters (`../index.md` ou `../`).
        assert "../index.md" in content or "(../)" in content, (
            "docs/starters/premier-crud/index.md doit comporter "
            "un lien retour vers la vue d'ensemble des starters."
        )


# ── Absence des commandes interdites sur TOUTES les pages starters ────────────


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("slug", ALL_STARTER_PAGES)
    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, slug: str, forbidden: str):
        content = _doc_path(slug).read_text(encoding="utf-8")
        assert forbidden not in content, (
            f"`{forbidden}` ne doit pas apparaître dans "
            f"docs/starters/{slug}/index.md "
            "(STARTER-SEQUENTIAL-NAV-001 : la page suppose que "
            "l'utilisateur est déjà dans un projet créé avec ce "
            "starter — les commandes d'installation/création vivent "
            "dans la doc globale, pas dans la page pédagogique)."
        )


# ── Absence des numéros de starter (7→14) dans les pages pédagogiques ─────────


class TestNumericLabelsAbsent:
    """Les pages pédagogiques (paliers 1→8) ne doivent plus présenter
    les starters par leur numéro (« Starter 7 » … « Starter 14 »).
    Les numéros restent confinés à `starter.json` + tests techniques.
    """

    @pytest.mark.parametrize("slug", PEDAGOGICAL_PAGES)
    @pytest.mark.parametrize("number", [7, 8, 9, 10, 11, 12, 13, 14])
    def test_no_numeric_starter_label(self, slug: str, number: int):
        content = _doc_path(slug).read_text(encoding="utf-8")
        # On match « Starter N » (suivi d'un espace, fin de ligne,
        # ponctuation…) pour ne pas attraper « Starter 100 » par
        # erreur.
        import re
        pattern = rf"Starter {number}\b"
        match = re.search(pattern, content)
        assert match is None, (
            f"docs/starters/{slug}/index.md contient « Starter "
            f"{number} » : les pages pédagogiques (paliers 1→8) ne "
            "doivent plus présenter les starters par leur numéro "
            "(STARTER-SEQUENTIAL-NAV-001)."
        )
