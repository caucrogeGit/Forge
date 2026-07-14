"""Tests documentaires — STARTER-ROADMAP-PROGRESSION-001.

Verrouille la progression pédagogique officielle des starters Forge :

- `docs/starters/index.md` doit présenter la section
  « Progression recommandée » avec les 11 paliers du niveau débutant ;
- `docs/starters/welcome-forge/debutant/welcome.md` ne doit plus recommander
  directement le starter Contacts CRUD comme étape immédiate ;
- `docs/guide/bonjour-forge.md` doit afficher l'avertissement
  « Ne sautez pas directement vers le CRUD Contacts » ;
- `docs/guide/getting-started.md` doit pointer vers la progression ;
- la roadmap mentionne `STARTER-ROADMAP-PROGRESSION-001` livré.

Depuis ADR-025 (STARTER-WELCOME-FORGE-TUTORIAL-ADR-025), le niveau débutant
est un **tutoriel continu manuel** : la progression liste les 11 paliers sans
les présenter comme des starters buildables (`forge starter:build`). Les
mentions « livré — starter `x` » ont donc été retirées de l'index ; seule la
présence des libellés de paliers reste verrouillée.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"
STARTER_WELCOME = PROJECT_ROOT / "docs" / "starters" / "welcome-forge" / "debutant" / "welcome.md"
BONJOUR_FORGE = PROJECT_ROOT / "docs" / "guide" / "bonjour-forge.md"
GETTING_STARTED = PROJECT_ROOT / "docs" / "guide" / "getting-started.md"
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
        "Réponse JSON",
        "Le jeton CSRF",
        "Premier formulaire POST",
        "Validation serveur",
        "Première base SQL",
        "Écrire en base",
    ])
    def test_steps_listed(self, step_label):
        assert step_label in self.content, (
            f"La progression doit lister le palier « {step_label} »."
        )

    def test_les_11_paliers_numerotes(self):
        # La progression reste numérotée 1 à 11 (ordre pédagogique stable),
        # même si les paliers ne sont plus des starters buildables (ADR-025).
        for n in range(1, 12):
            assert f"{n}. **" in self.content, (
                f"Le palier numéroté « {n}. ** » doit figurer dans la "
                "progression de docs/starters/index.md."
            )


# ── docs/starters/welcome-forge/debutant/welcome.md : ne renvoie plus directement vers CRUD ────


class TestWelcomeStarterRedirectsToProgression:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = STARTER_WELCOME.read_text(encoding="utf-8")

    def test_no_immediate_crud_recommendation(self):
        forbidden = "passez au **Starter 1 — Contacts**"
        assert forbidden not in self.content, (
            f"La phrase « {forbidden} » suggère un saut direct vers "
            "le CRUD Contacts et doit être retirée "
            "(STARTER-ROADMAP-PROGRESSION-001)."
        )

    def test_points_to_next_palier(self):
        assert "query-params.md" in self.content, (
            "La section « Après ce palier » de welcome doit pointer "
            "directement vers le palier suivant (query-params)."
        )

    def test_does_not_label_contacts_as_advanced_anymore(self):
        assert "Starter 1 — Contacts" not in self.content, (
            "welcome ne doit plus mentionner « Starter 1 — Contacts » "
            "directement (la progression passe par les paliers "
            "intermédiaires)."
        )


# ── docs/guide/bonjour-forge.md : admonition d'avertissement ─────────────────────────


class TestBonjourForgeWarning:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = BONJOUR_FORGE.read_text(encoding="utf-8")

    def test_warning_admonition_present(self):
        assert '!!! info "Ne sautez pas directement vers le CRUD Contacts"' in self.content, (
            "docs/guide/bonjour-forge.md doit afficher l'admonition "
            "« Ne sautez pas directement vers le CRUD Contacts »."
        )

    def test_links_to_progression_anchor(self):
        assert "starters/index.md#progression-recommandee" in self.content, (
            "L'admonition (ou la table « Aller plus loin ») doit "
            "pointer vers l'ancre #progression-recommandee."
        )

    def test_progression_row_in_table(self):
        assert "Progression officielle des starters" in self.content, (
            "La table « Aller plus loin » doit comporter une ligne "
            "« Progression officielle des starters »."
        )


# ── docs/guide/getting-started.md : bullet vers la progression ───────────────────────


class TestGettingStartedPointsToProgression:

    def test_progression_bullet_present(self):
        text = GETTING_STARTED.read_text(encoding="utf-8")
        assert "Progression officielle des starters" in text, (
            "docs/guide/getting-started.md doit pointer vers la progression "
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
        lines = [
            line for line in text.splitlines()
            if "STARTER-ROADMAP-PROGRESSION-001" in line
        ]
        assert any("**livré**" in line for line in lines), (
            "STARTER-ROADMAP-PROGRESSION-001 doit être marqué « livré » "
            "dans la roadmap."
        )
