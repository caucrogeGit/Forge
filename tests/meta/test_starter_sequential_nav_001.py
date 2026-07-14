"""Tests documentaires — STARTER-SEQUENTIAL-NAV-001.

Verrouille la navigation pédagogique séquentielle entre pages de
starters. Chaque palier pointe vers le suivant (fichier frère
``<slug>.md`` au sein du dossier de niveau). Le **dernier palier** d'un
niveau pointe vers le **bilan du niveau** (``bilan.md``, page sœur), et
ce bilan renvoie au premier palier du niveau suivant s'il existe, sinon
au ``recapitulatif.md`` à la racine du starter (STARTERS-DOC-LEVELS).

Vérifie aussi :

- absence des commandes de création/installation interdites dans
  TOUTES les pages `docs/starters/*/index.md` (``forge starter:build``,
  ``forge new mon-projet``, ``cd mon-projet``,
  ``source .venv/bin/activate``) ;
- absence des étiquettes par numéro (Starter 7…14) dans les pages
  pédagogiques (welcome → first-sql). first-crud-generated peut garder
  son numéro historique « 1 » (pas dans la plage 7–14 protégée).
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


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
}

# Pages pédagogiques (paliers 1→11). `first-sql-write` est le dernier palier
# du niveau : il n'a pas de palier suivant dans le chaînage (il pointe vers le
# bilan du niveau), mais reste une page pédagogique à part entière.
PEDAGOGICAL_PAGES = list(SEQUENTIAL_CHAIN.keys()) + ["first-sql-write"]

# Plus aucun starter autonome de sujet CRUD dans la doc : les starters
# first-crud / first-crud-generated ont été retirés (le dossier-sujet crud/
# n'existe plus).
STANDALONE_STARTERS: list[str] = []

TOPIC_DOC_PATHS: dict[str, str] = {}

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
    # docs/starters/welcome-forge/<slug>.md. Les starters CRUD autonomes vivent
    # sous le dossier-sujet crud/ (voir TOPIC_DOC_PATHS).
    if slug in TOPIC_DOC_PATHS:
        return STARTERS_DOCS / TOPIC_DOC_PATHS[slug]
    if slug in STANDALONE_STARTERS:
        return STARTERS_DOCS / slug / "index.md"
    return STARTERS_DOCS / "welcome-forge" / "debutant" / f"{slug}.md"


# ── Chaînage séquentiel : chaque page pointe vers la suivante ─────────────────


class TestSequentialChain:

    @pytest.mark.parametrize("source,target", list(SEQUENTIAL_CHAIN.items()))
    def test_page_points_to_next_palier(self, source: str, target: str):
        page = _doc_path(source)
        content = page.read_text(encoding="utf-8")
        # DOCS-STARTERS-PROGRESSION-FOLDER-001 — au sein de welcome/, le
        # palier suivant est un fichier frère « target.md » ; le dernier
        # palier (first-sql-write) pointe vers le starter autonome
        # first-crud sous le dossier-sujet crud/ (« ../crud/first-crud.md »).
        if target in TOPIC_DOC_PATHS:
            # Lien vers la page sous dossier-sujet (« ../crud/first-crud.md »).
            link_variants = (f"../{TOPIC_DOC_PATHS[target]}",)
        elif target in STANDALONE_STARTERS:
            link_variants = (f"../{target}/", f"../{target}/index.md")
        else:
            link_variants = (f"{target}.md", f"{target}/")
        assert any(v in content for v in link_variants), (
            f"{page} doit contenir un lien vers le palier suivant "
            f"« {link_variants[0]} » (STARTER-SEQUENTIAL-NAV-001)."
        )

    def test_last_palier_points_to_level_bilan(self):
        # STARTERS-DOC-LEVELS — le dernier palier d'un niveau pointe vers le
        # bilan DU NIVEAU (page sœur dans le dossier du niveau), pas vers un
        # starter autonome.
        content = _doc_path("first-sql-write").read_text(encoding="utf-8")
        assert "(bilan.md)" in content, (
            "Le dernier palier (first-sql-write) doit pointer vers le bilan "
            "du niveau (`bilan.md`) — STARTERS-DOC-LEVELS."
        )

    def test_debutant_bilan_points_to_next_level(self):
        # Le niveau intermédiaire existe : le bilan débutant renvoie à son
        # premier palier (`../intermediaire/list-records.md`), pas au
        # récapitulatif.
        bilan = STARTERS_DOCS / "welcome-forge" / "debutant" / "bilan.md"
        content = bilan.read_text(encoding="utf-8")
        assert "../intermediaire/list-records.md" in content, (
            "Le bilan débutant doit renvoyer au premier palier du niveau "
            "intermédiaire (next-level wiring) — STARTERS-DOC-LEVELS."
        )

    def test_intermediaire_last_palier_points_to_level_bilan(self):
        # Dernier palier intermédiaire (ADR-028, mini-projet Carnet de notes) →
        # bilan du niveau. Le dernier palier est désormais session-state.
        page = STARTERS_DOCS / "welcome-forge" / "intermediaire" / "session-state.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_intermediaire_bilan_points_to_next_level(self):
        # Le niveau avancé existe : le bilan intermédiaire renvoie à son
        # premier palier (`../avance/relations.md`), pas au récapitulatif.
        bilan = STARTERS_DOCS / "welcome-forge" / "intermediaire" / "bilan.md"
        assert "../avance/relations.md" in bilan.read_text(encoding="utf-8")

    def test_avance_relations_points_to_db_transaction(self):
        # ADR-028, mini-projet Catalogue d'articles. Palier 1 → palier 2.
        page = STARTERS_DOCS / "welcome-forge" / "avance" / "relations.md"
        assert "(db-transaction.md)" in page.read_text(encoding="utf-8")

    def test_avance_db_transaction_points_to_json_api(self):
        # ADR-042 : le palier upload (opt-in forge-mvc-files) a été retiré.
        # Palier 2 avancé → palier 3 (json-api).
        page = STARTERS_DOCS / "welcome-forge" / "avance" / "db-transaction.md"
        assert "(json-api.md)" in page.read_text(encoding="utf-8")

    def test_avance_last_palier_points_to_level_bilan(self):
        # Dernier palier avancé (json-api) → bilan du niveau.
        page = STARTERS_DOCS / "welcome-forge" / "avance" / "json-api.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_avance_bilan_points_to_recapitulatif(self):
        # Dernier niveau → le bilan avancé renvoie au récapitulatif à la
        # racine du starter.
        bilan = STARTERS_DOCS / "welcome-forge" / "avance" / "bilan.md"
        assert "../recapitulatif.md" in bilan.read_text(encoding="utf-8")

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
