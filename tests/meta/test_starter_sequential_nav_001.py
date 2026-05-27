"""Tests documentaires — STARTER-SEQUENTIAL-NAV-001.

Verrouille la navigation pédagogique séquentielle entre pages de
starters. Chaque page pointe vers le palier suivant via un lien
``../<slug>/`` (ou ``../<slug>/index.md``) dans une section
« Après ce starter ». La page Contacts CRUD clôt la chaîne et
renvoie vers la vue d'ensemble.

Vérifie aussi :

- absence des commandes de création/installation interdites dans
  TOUTES les pages `docs/starters/*/index.md` (``forge starter:build``,
  ``forge new mon-projet``, ``cd mon-projet``,
  ``source .venv/bin/activate``) ;
- absence des étiquettes par numéro (Starter 7…14) dans les pages
  pédagogiques (welcome → first-sql). 01-contact-simple peut garder
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
    "request-debug": "form-post",
    "form-post": "server-validation",
    "server-validation": "first-sql",
    "first-sql": "01-contact-simple",
}

# Pages pédagogiques (paliers 1→8). 01-contact-simple est exclu :
# elle peut garder des étiquettes historiques propres ("Starter 1").
PEDAGOGICAL_PAGES = list(SEQUENTIAL_CHAIN.keys())

# Toutes les pages starters concernées par la règle stricte
# d'absence des commandes de création.
ALL_STARTER_PAGES = PEDAGOGICAL_PAGES + ["01-contact-simple"]

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _doc_path(slug: str) -> Path:
    return STARTERS_DOCS / slug / "index.md"


# ── Chaînage séquentiel : chaque page pointe vers la suivante ─────────────────


class TestSequentialChain:

    @pytest.mark.parametrize("source,target", list(SEQUENTIAL_CHAIN.items()))
    def test_page_points_to_next_palier(self, source: str, target: str):
        page = _doc_path(source)
        content = page.read_text(encoding="utf-8")
        # On accepte les deux formats : ../target/  ou  ../target/index.md
        link_variants = (f"../{target}/", f"../{target}/index.md")
        assert any(v in content for v in link_variants), (
            f"docs/starters/{source}/index.md doit contenir un lien "
            f"vers le palier suivant : « ../{target}/ » "
            f"(STARTER-SEQUENTIAL-NAV-001)."
        )

    def test_first_sql_points_to_contacts_crud(self):
        # Cas spécifique mentionné dans le ticket : first-sql →
        # 01-contact-simple (cf. SEQUENTIAL_CHAIN, redondant mais explicite).
        content = _doc_path("first-sql").read_text(encoding="utf-8")
        assert "../01-contact-simple/" in content

    def test_contacts_crud_returns_to_overview(self):
        # 01-contact-simple clôt la progression et renvoie vers ../
        content = _doc_path("01-contact-simple").read_text(encoding="utf-8")
        # On cherche un lien retour explicite vers la vue d'ensemble
        # des starters (`../index.md` ou `../`).
        assert "../index.md" in content or "(../)" in content, (
            "docs/starters/01-contact-simple/index.md doit comporter "
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
