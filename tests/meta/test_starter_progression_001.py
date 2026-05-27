"""Tests documentaires — STARTER-ROADMAP-PROGRESSION-001.

Verrouille la progression pédagogique officielle des starters Forge :

- `docs/starters/index.md` doit présenter la section
  « Progression recommandée » avec les 9 paliers et les codes
  des tickets futurs ;
- `docs/starters/welcome/index.md` ne doit plus recommander
  directement le starter Contacts CRUD comme étape immédiate ;
- `docs/bonjour-forge.md` doit afficher l'avertissement
  « Ne sautez pas directement vers le CRUD Contacts » ;
- `docs/getting-started.md` doit pointer vers la progression ;
- la roadmap mentionne `STARTER-ROADMAP-PROGRESSION-001` livré.

Le ticket n'a pas créé les starters intermédiaires : les codes
`STARTER-*-001` sont volontairement présentés comme trajectoire
future, non comme starters disponibles aujourd'hui.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"
STARTER_WELCOME = PROJECT_ROOT / "docs" / "starters" / "welcome" / "index.md"
BONJOUR_FORGE = PROJECT_ROOT / "docs" / "bonjour-forge.md"
GETTING_STARTED = PROJECT_ROOT / "docs" / "getting-started.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


# ── Section « Progression recommandée » dans docs/starters/index.md ────────────


class TestProgressionSectionInStartersIndex:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = STARTERS_INDEX.read_text(encoding="utf-8")

    def test_section_header_present(self):
        assert "## Progression recommandée" in self.content, (
            "docs/starters/index.md doit comporter une section "
            "« ## Progression recommandée »."
        )

    @pytest.mark.parametrize("step_label", [
        "Bonjour Forge",
        "Paramètres d'URL",
        "Première vue HTML",
        "Route dynamique",
        "Inspecter une requête",
        "Premier formulaire POST",
        "Validation serveur",
        "Première base SQL",
        "Premier CRUD",
    ])
    def test_9_steps_listed(self, step_label):
        assert step_label in self.content, (
            f"La progression doit lister le palier « {step_label} »."
        )

    @pytest.mark.parametrize("ticket_code", [
        # STARTER-QUERY-PARAMS-001 livré → voir test_palier_2_livre.
        # STARTER-FIRST-HTML-VIEW-001 livré → voir test_palier_3_livre.
        # STARTER-DYNAMIC-ROUTE-001 livré → voir test_palier_4_livre.
        # STARTER-REQUEST-DEBUG-001 livré → voir test_palier_5_livre.
        # STARTER-FORM-POST-001 livré → voir test_palier_6_livre.
        # STARTER-SERVER-VALIDATION-001 livré → voir test_palier_7_livre.
        "STARTER-FIRST-SQL-001",
        "STARTER-CONTACTS-CRUD-REPOSITION-001",
    ])
    def test_future_ticket_codes_listed(self, ticket_code):
        assert ticket_code in self.content, (
            f"Le ticket futur {ticket_code} doit être inscrit comme "
            "trajectoire dans la progression."
        )

    def test_palier_2_query_params_marque_livre(self):
        # STARTER-QUERY-PARAMS-001 est livré : palier 2 doit l'indiquer
        # explicitement avec la mention « livré ».
        # On vise l'item numéroté de la progression (« 2. **Paramètres
        # d'URL** ») pour éviter de matcher la ligne du tableau de
        # synthèse qui répète le même nom.
        assert "STARTER-QUERY-PARAMS-001" in self.content, (
            "STARTER-QUERY-PARAMS-001 doit rester référencé dans la "
            "progression (palier 2)."
        )
        text = self.content
        idx_palier2 = text.find("2. **Paramètres d'URL**")
        idx_palier3 = text.find("3. **Première vue HTML**")
        assert idx_palier2 != -1, (
            "Item « 2. **Paramètres d'URL** » introuvable dans la progression."
        )
        assert idx_palier3 != -1, (
            "Item « 3. **Première vue HTML** » introuvable dans la progression."
        )
        palier2_block = text[idx_palier2:idx_palier3]
        assert "livré" in palier2_block, (
            "Le palier 2 (Paramètres d'URL) doit être marqué « livré » "
            "depuis STARTER-QUERY-PARAMS-001."
        )
        assert "query-params" in palier2_block, (
            "Le palier 2 doit mentionner le starter `query-params`."
        )

    def test_palier_3_first_html_view_marque_livre(self):
        # STARTER-FIRST-HTML-VIEW-001 livré : palier 3 doit l'indiquer
        # explicitement avec la mention « livré ».
        # Cf. test_palier_2 — on ancre sur l'item numéroté.
        assert "STARTER-FIRST-HTML-VIEW-001" in self.content, (
            "STARTER-FIRST-HTML-VIEW-001 doit rester référencé dans la "
            "progression (palier 3)."
        )
        text = self.content
        idx_palier3 = text.find("3. **Première vue HTML**")
        idx_palier4 = text.find("4. **Route dynamique**")
        assert idx_palier3 != -1, (
            "Item « 3. **Première vue HTML** » introuvable dans la progression."
        )
        assert idx_palier4 != -1, (
            "Item « 4. **Route dynamique** » introuvable dans la progression."
        )
        palier3_block = text[idx_palier3:idx_palier4]
        assert "livré" in palier3_block, (
            "Le palier 3 (Première vue HTML) doit être marqué « livré » "
            "depuis STARTER-FIRST-HTML-VIEW-001."
        )
        assert "first-html-view" in palier3_block, (
            "Le palier 3 doit mentionner le starter `first-html-view`."
        )

    def test_palier_4_dynamic_route_marque_livre(self):
        # STARTER-DYNAMIC-ROUTE-001 livré : palier 4 doit l'indiquer
        # explicitement avec la mention « livré ».
        # Cf. test_palier_2/3 — on ancre sur l'item numéroté.
        assert "STARTER-DYNAMIC-ROUTE-001" in self.content, (
            "STARTER-DYNAMIC-ROUTE-001 doit rester référencé dans la "
            "progression (palier 4)."
        )
        text = self.content
        idx_palier4 = text.find("4. **Route dynamique**")
        idx_palier5 = text.find("5. **Inspecter une requête**")
        assert idx_palier4 != -1, (
            "Item « 4. **Route dynamique** » introuvable dans la progression."
        )
        assert idx_palier5 != -1, (
            "Item « 5. **Inspecter une requête** » introuvable dans la progression."
        )
        palier4_block = text[idx_palier4:idx_palier5]
        assert "livré" in palier4_block, (
            "Le palier 4 (Route dynamique) doit être marqué « livré » "
            "depuis STARTER-DYNAMIC-ROUTE-001."
        )
        assert "dynamic-route" in palier4_block, (
            "Le palier 4 doit mentionner le starter `dynamic-route`."
        )

    def test_palier_5_request_debug_marque_livre(self):
        # STARTER-REQUEST-DEBUG-001 livré : palier 5 doit l'indiquer
        # explicitement avec la mention « livré ».
        assert "STARTER-REQUEST-DEBUG-001" in self.content, (
            "STARTER-REQUEST-DEBUG-001 doit rester référencé dans la "
            "progression (palier 5)."
        )
        text = self.content
        idx_palier5 = text.find("5. **Inspecter une requête**")
        idx_palier6 = text.find("6. **Premier formulaire POST**")
        assert idx_palier5 != -1, (
            "Item « 5. **Inspecter une requête** » introuvable dans la progression."
        )
        assert idx_palier6 != -1, (
            "Item « 6. **Premier formulaire POST** » introuvable dans la progression."
        )
        palier5_block = text[idx_palier5:idx_palier6]
        assert "livré" in palier5_block, (
            "Le palier 5 (Inspecter une requête) doit être marqué « livré » "
            "depuis STARTER-REQUEST-DEBUG-001."
        )
        assert "request-debug" in palier5_block, (
            "Le palier 5 doit mentionner le starter `request-debug`."
        )

    def test_palier_6_form_post_marque_livre(self):
        # STARTER-FORM-POST-001 livré : palier 6 doit l'indiquer
        # explicitement avec la mention « livré ».
        assert "STARTER-FORM-POST-001" in self.content, (
            "STARTER-FORM-POST-001 doit rester référencé dans la "
            "progression (palier 6)."
        )
        text = self.content
        idx_palier6 = text.find("6. **Premier formulaire POST**")
        idx_palier7 = text.find("7. **Validation serveur**")
        assert idx_palier6 != -1, (
            "Item « 6. **Premier formulaire POST** » introuvable dans la progression."
        )
        assert idx_palier7 != -1, (
            "Item « 7. **Validation serveur** » introuvable dans la progression."
        )
        palier6_block = text[idx_palier6:idx_palier7]
        assert "livré" in palier6_block, (
            "Le palier 6 (Premier formulaire POST) doit être marqué « livré » "
            "depuis STARTER-FORM-POST-001."
        )
        assert "form-post" in palier6_block, (
            "Le palier 6 doit mentionner le starter `form-post`."
        )

    def test_palier_7_server_validation_marque_livre(self):
        # STARTER-SERVER-VALIDATION-001 livré : palier 7 doit
        # l'indiquer explicitement avec la mention « livré ».
        assert "STARTER-SERVER-VALIDATION-001" in self.content, (
            "STARTER-SERVER-VALIDATION-001 doit rester référencé dans "
            "la progression (palier 7)."
        )
        text = self.content
        idx_palier7 = text.find("7. **Validation serveur**")
        idx_palier8 = text.find("8. **Première base SQL**")
        assert idx_palier7 != -1, (
            "Item « 7. **Validation serveur** » introuvable dans la progression."
        )
        assert idx_palier8 != -1, (
            "Item « 8. **Première base SQL** » introuvable dans la progression."
        )
        palier7_block = text[idx_palier7:idx_palier8]
        assert "livré" in palier7_block, (
            "Le palier 7 (Validation serveur) doit être marqué « livré » "
            "depuis STARTER-SERVER-VALIDATION-001."
        )
        assert "server-validation" in palier7_block, (
            "Le palier 7 doit mentionner le starter `server-validation`."
        )

    def test_warning_admonition_present(self):
        # Le saut welcome → CRUD est explicitement mis en garde
        assert "!!! warning" in self.content, (
            "Une admonition !!! warning doit signaler le saut "
            "welcome → Contacts CRUD."
        )
        assert "Saut Bonjour Forge → Contacts CRUD" in self.content, (
            "L'admonition warning doit nommer explicitement le saut "
            "« Bonjour Forge → Contacts CRUD »."
        )


# ── docs/starters/welcome/index.md : ne renvoie plus directement vers CRUD ────


class TestWelcomeStarterRedirectsToProgression:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = STARTER_WELCOME.read_text(encoding="utf-8")

    def test_no_immediate_crud_recommendation(self):
        # La phrase « passez au Starter 1 — Contacts pour un premier
        # CRUD complet » ne doit plus exister.
        forbidden = "passez au **Starter 1 — Contacts**"
        assert forbidden not in self.content, (
            f"La phrase « {forbidden} » suggère un saut direct vers "
            "le CRUD Contacts et doit être retirée "
            "(STARTER-ROADMAP-PROGRESSION-001)."
        )

    def test_points_to_progression(self):
        assert "Progression recommandée des starters" in self.content, (
            "La section « Après ce starter » doit pointer vers la "
            "« Progression recommandée des starters »."
        )

    def test_mentions_progression_anchor(self):
        assert "../index.md#progression-recommandee" in self.content, (
            "Le lien vers la progression doit cibler l'ancre "
            "#progression-recommandee de starters/index.md."
        )

    def test_contacts_labeled_as_advanced(self):
        # Quand Contacts reste mentionné, c'est comme « niveau avancé »
        assert "niveau avancé" in self.content, (
            "Le lien vers Starter 1 — Contacts doit être étiqueté "
            "« niveau avancé » pour éviter l'effet d'étape immédiate."
        )


# ── docs/bonjour-forge.md : admonition d'avertissement ─────────────────────────


class TestBonjourForgeWarning:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = BONJOUR_FORGE.read_text(encoding="utf-8")

    def test_warning_admonition_present(self):
        assert '!!! info "Ne sautez pas directement vers le CRUD Contacts"' in self.content, (
            "docs/bonjour-forge.md doit afficher l'admonition "
            "« Ne sautez pas directement vers le CRUD Contacts »."
        )

    def test_links_to_progression_anchor(self):
        assert "starters/index.md#progression-recommandee" in self.content, (
            "L'admonition (ou la table « Aller plus loin ») doit "
            "pointer vers l'ancre #progression-recommandee."
        )

    def test_progression_row_in_table(self):
        # Une ligne du tableau « Aller plus loin » mène à la progression
        assert "Progression officielle des starters" in self.content, (
            "La table « Aller plus loin » doit comporter une ligne "
            "« Progression officielle des starters »."
        )


# ── docs/getting-started.md : bullet vers la progression ───────────────────────


class TestGettingStartedPointsToProgression:

    def test_progression_bullet_present(self):
        text = GETTING_STARTED.read_text(encoding="utf-8")
        assert "Progression officielle des starters" in text, (
            "docs/getting-started.md doit pointer vers la progression "
            "officielle dans son Étape 3 (« Continuer »)."
        )
        assert "starters/index.md#progression-recommandee" in text, (
            "Le bullet progression doit cibler l'ancre "
            "#progression-recommandee."
        )


# ── Roadmap : ticket marqué livré ──────────────────────────────────────────────


class TestRoadmapEntry:

    def test_ticket_listed_as_delivered(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "STARTER-ROADMAP-PROGRESSION-001" in text, (
            "La roadmap doit mentionner STARTER-ROADMAP-PROGRESSION-001."
        )
        # L'entrée doit être marquée « livré »
        # (le ticket est sur sa propre ligne du tableau)
        lines = [
            line for line in text.splitlines()
            if "STARTER-ROADMAP-PROGRESSION-001" in line
        ]
        assert any("**livré**" in line for line in lines), (
            "STARTER-ROADMAP-PROGRESSION-001 doit être marqué « livré » "
            "dans la roadmap."
        )


# ── Intermédiaires non créés : pas de starter:build / pyproject pour ces codes ─


class TestFutureStartersNotYetCreated:
    """Les starters intermédiaires sont des trajectoires futures, pas des
    starters existants. Aucun fichier sous `forge_cli/starters/data/`
    ne doit avoir été ajouté par ce ticket."""

    @pytest.mark.parametrize("future_starter_slug", [
        # query-params retiré : livré par STARTER-QUERY-PARAMS-001 (palier 2).
        # first-html-view retiré : livré par STARTER-FIRST-HTML-VIEW-001 (palier 3).
        # dynamic-route retiré : livré par STARTER-DYNAMIC-ROUTE-001 (palier 4).
        # request-debug retiré : livré par STARTER-REQUEST-DEBUG-001 (palier 5).
        # form-post retiré : livré par STARTER-FORM-POST-001 (palier 6).
        # server-validation retiré : livré par STARTER-SERVER-VALIDATION-001 (palier 7).
        "first-sql",
    ])
    def test_future_starter_not_created(self, future_starter_slug):
        starter_dir = (
            PROJECT_ROOT
            / "forge_cli"
            / "starters"
            / "data"
            / future_starter_slug
        )
        assert not starter_dir.exists(), (
            f"Le starter '{future_starter_slug}' ne doit PAS être créé "
            "par ce ticket — c'est un ticket futur séparé. Trouvé : "
            f"{starter_dir}"
        )
