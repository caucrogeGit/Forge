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
        "STARTER-QUERY-PARAMS-001",
        "STARTER-FIRST-HTML-VIEW-001",
        "STARTER-DYNAMIC-ROUTE-001",
        "STARTER-REQUEST-DEBUG-001",
        "STARTER-FORM-POST-001",
        "STARTER-SERVER-VALIDATION-001",
        "STARTER-FIRST-SQL-001",
        "STARTER-CONTACTS-CRUD-REPOSITION-001",
    ])
    def test_future_ticket_codes_listed(self, ticket_code):
        assert ticket_code in self.content, (
            f"Le ticket futur {ticket_code} doit être inscrit comme "
            "trajectoire dans la progression."
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
        "query-params",
        "first-html-view",
        "dynamic-route",
        "request-debug",
        "form-post",
        "server-validation",
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
