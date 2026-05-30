"""Tests documentaires — STARTER-QUERY-PARAMS-001.

Verrouille le contrat documentaire de la page
`docs/starters/progression/query-params.md` : elle doit présenter le palier 2
de la progression officielle (Paramètres d'URL) avec un parcours
pédagogique minimal — `request.param(...)`, deux routes, aucune vue
HTML, aucune base de données.

La navigation MkDocs doit lister la page sous « Modules et starters » et
le tableau de synthèse de `docs/starters/index.md` doit l'intégrer.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
DOC = PROJECT_ROOT / "docs" / "starters" / "progression" / "query-params.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


# ── Existence et structure de base ────────────────────────────────────────────


class TestQueryParamsDocExistence:

    def test_doc_existe(self):
        assert DOC.exists(), "docs/starters/progression/query-params.md doit exister"

    def test_doc_non_vide(self):
        assert len(_text()) > 500

    def test_titre_h1(self):
        assert _text().startswith("# Paramètres d'URL"), (
            "Le titre H1 doit être « # Paramètres d'URL »."
        )

    def test_doc_courte(self):
        """La doc reste courte (objectif ~80-150 lignes)."""
        lines = _text().splitlines()
        assert len(lines) <= 200, (
            f"La doc query-params doit rester courte ; {len(lines)} lignes."
        )


# ── Contenu pédagogique attendu ───────────────────────────────────────────────


class TestQueryParamsDocContent:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("marker", [
        "query-params",
        "palier 2",
        "Bonjour Forge",
        "/query-params",
        "/query-params/hello",
        "QueryParamsController",
        'request.param("name", default="Forge")',
        "Bonjour Roger",
        # `forge starter:build query-params` retiré de cette liste par
        # STARTER-SEQUENTIAL-NAV-001 : les pages starters ne doivent
        # plus contenir AUCUNE commande `forge starter:build` ; la
        # création/application du starter est faite depuis la doc
        # globale (cli-commands.md), pas depuis la page pédagogique.
    ])
    def test_contenu_attendu_present(self, marker: str):
        assert marker in self.content, (
            f"La doc query-params doit mentionner '{marker}'."
        )

    def test_mentionne_palier_suivant(self):
        # STARTER-SEQUENTIAL-NAV-001 : le pointeur vers le palier
        # suivant utilise le lien direct `../first-html-view/...`
        # plutôt qu'un code de ticket (mis en place avant que le
        # starter ne soit livré ; désormais le starter existe).
        assert "first-html-view.md" in self.content, (
            "La doc doit pointer directement vers le palier suivant "
            "(`../first-html-view/index.md`)."
        )

    def test_lien_vers_progression(self):
        # La doc renvoie vers la section #progression-recommandee
        assert "../index.md#progression-recommandee" in self.content, (
            "La doc doit pointer vers la progression officielle."
        )


# ── Notions volontairement repoussées (paliers ultérieurs) ────────────────────


class TestQueryParamsDocNoise:
    """Le starter query-params reste minimal : pas de Jinja2, pas de
    formulaire POST, pas de validation, pas de SQL — ces notions sont
    repoussées à leurs propres starters (paliers 3 à 8)."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = _text()

    @pytest.mark.parametrize("noise", [
        # `BaseController.render` retiré de cette liste par
        # STARTER-SEQUENTIAL-NAV-001 : la section « Après ce starter »
        # tease explicitement le palier suivant (Première vue HTML)
        # en montrant son API-clé. Acceptable comme forward
        # reference courte.
        "Response.debug",
        "<form",
        "POST",
        "MariaDB",
        "migration",
        "CRUD",
        "Tailwind",
        "Mermaid",
    ])
    def test_notion_repoussee_absente(self, noise: str):
        assert noise not in self.content, (
            f"`{noise}` ne doit pas apparaître dans le starter "
            "query-params (repoussé à un futur palier)."
        )


# ── Intégration : navigation MkDocs et tableau de synthèse ────────────────────


class TestQueryParamsDocIntegration:

    def test_starters_index_lit_le_starter_dans_la_table(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        assert "[Paramètres d'URL](progression/query-params.md)" in text, (
            "docs/starters/index.md doit lister Paramètres d'URL dans "
            "le tableau de synthèse."
        )

    def test_starters_index_palier_2_marque_livre(self):
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        # Le palier 2 référence le starter query-params comme livré
        assert "starter `query-params`" in text, (
            "La progression doit nommer le starter `query-params` comme livré."
        )

    def test_mkdocs_nav_inclut_query_params(self):
        text = MKDOCS.read_text(encoding="utf-8")
        assert "starters/progression/query-params.md" in text, (
            "mkdocs.yml doit lister la page dans la nav."
        )

    def test_mkdocs_nav_label_parametres_url(self):
        text = MKDOCS.read_text(encoding="utf-8")
        assert "Paramètres d'URL:" in text, (
            "mkdocs.yml doit utiliser le label « Paramètres d'URL » "
            "pour le starter."
        )

    def test_roadmap_lists_ticket_as_delivered(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "STARTER-QUERY-PARAMS-001" in text, (
            "La roadmap doit mentionner STARTER-QUERY-PARAMS-001."
        )
        lines = [
            line for line in text.splitlines()
            if "STARTER-QUERY-PARAMS-001" in line
        ]
        # Au moins une ligne où le ticket est marqué livré
        assert any("**livré**" in line for line in lines), (
            "STARTER-QUERY-PARAMS-001 doit être marqué « livré »."
        )


# ── Anti-régression : aucun numéro de starter dans les pages pédagogiques ─────


class TestQueryParamsDocAntiRegression:
    """L'identité publique du starter est `query-params` / « Paramètres
    d'URL ». Les numéros internes (`number: 8`) doivent rester confinés
    à `starter.json` et aux tests techniques — jamais dans les pages
    pédagogiques. Cette classe verrouille l'absence des formulations
    qui poussent le numéro ou du boilerplate shell comme repère
    utilisateur."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = DOC.read_text(encoding="utf-8")

    @pytest.mark.parametrize("forbidden", [
        "Starter 8",
        "starter:build 8",
        "forge new mon-projet",
        "source .venv/bin/activate",
    ])
    def test_forbidden_pattern_absent_in_query_params_doc(self, forbidden: str):
        assert forbidden not in self.content, (
            f"La doc query-params ne doit pas contenir '{forbidden}'. "
            "L'identité publique reste `query-params` / « Paramètres "
            "d'URL »."
        )

    def test_starters_index_no_starter_8_as_pedagogical_name(self):
        # docs/starters/index.md ne doit jamais présenter « Starter 8 »
        # comme nom pédagogique (entête de section, titre de carte…).
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        # Patterns à interdire (nom pédagogique, pas commande CLI)
        forbidden_patterns = [
            "### Starter 8",
            "Starter 8 — Paramètres",
            "Starter 8 -- Paramètres",
            "starter 8 (paramètres",
        ]
        found = [p for p in forbidden_patterns if p.lower() in text.lower()]
        assert not found, (
            f"docs/starters/index.md utilise « Starter 8 » comme nom "
            f"pédagogique : {found}. L'identité publique est "
            "« Paramètres d'URL » / `query-params`."
        )

    def test_starters_index_no_numbered_command_for_query_params(self):
        # Le catalogue automation ne doit pas pousser query-params via
        # son numéro : il s'applique par identifiant public.
        text = STARTERS_INDEX.read_text(encoding="utf-8")
        # Recherche d'une ligne qui combine starter:build 8 et un
        # commentaire mentionnant Paramètres d'URL ou query-params
        for line in text.splitlines():
            if "starter:build 8" in line and (
                "query-params" in line.lower()
                or "paramètres d'url" in line.lower()
            ):
                pytest.fail(
                    f"docs/starters/index.md mentionne query-params via "
                    f"`starter:build 8` : {line!r}. Utiliser "
                    "`forge starter:build query-params` à la place."
                )
