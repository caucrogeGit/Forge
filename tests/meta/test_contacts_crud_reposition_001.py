"""Tests documentaires — STARTER-CONTACTS-CRUD-REPOSITION-001.

Verrouille le repositionnement pédagogique du starter
`contact-simple` (Contacts CRUD) comme palier 12 — synthèse
avancée — de la progression officielle des starters.

- la progression officielle contient bien 9 paliers ;
- Contacts CRUD est marqué comme palier 12 dans la progression ;
- Contacts CRUD est décrit comme avancé / synthèse, pas comme
  étape immédiate après Bonjour Forge ;
- la page du starter Contacts liste les prérequis pédagogiques ;
- les anciennes étiquettes débutant/premier-parcours sont retirées
  comme **étiquettes du starter Contacts** (les mentions historiques
  dans d'autres contextes restent autorisées).
- la roadmap mentionne STARTER-CONTACTS-CRUD-REPOSITION-001 livré.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTACT_DOC = PROJECT_ROOT / "docs" / "starters" / "contact-simple" / "index.md"
STARTERS_INDEX = PROJECT_ROOT / "docs" / "starters" / "index.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _extract_contacts_section(text: str) -> str:
    """Extrait la section « Contacts » du catalogue
    `docs/starters/index.md` (entre son header et le header suivant)."""
    start_marker = "### Contacts"
    idx = text.find(start_marker)
    if idx == -1:
        return ""
    rest = text[idx + len(start_marker):]
    next_idx = rest.find("\n### ")
    if next_idx == -1:
        return text[idx:]
    return text[idx: idx + len(start_marker) + next_idx]


# ── Progression officielle ────────────────────────────────────────────────────


class TestProgressionAfterReposition:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = STARTERS_INDEX.read_text(encoding="utf-8")

    def test_progression_contient_les_11_paliers(self):
        # Chaque palier numéroté `N. **...**` doit être présent (1→11).
        for n in range(1, 12):
            assert f"{n}. **" in self.content, (
                f"Palier {n} introuvable dans la progression."
            )
        # Plus de 12e palier : le CRUD est un starter autonome, pas un palier.
        assert "12. **" not in self.content, (
            "La progression ne doit plus comporter de palier 12 : le CRUD "
            "est désormais le starter autonome `premier-crud`."
        )

    def test_apres_progression_premier_crud(self):
        # Après les 11 paliers, le premier starter autonome est Premier CRUD.
        assert "premier-crud/index.md" in self.content, (
            "La progression doit pointer vers le starter autonome "
            "`premier-crud` après le palier 11."
        )
        assert "STARTER-PREMIER-CRUD-001" in self.content, (
            "Le starter Premier CRUD (STARTER-PREMIER-CRUD-001) doit être "
            "cité comme premier starter autonome après la progression."
        )


# ── Repositionnement de la page Contacts (avancé / synthèse) ──────────────────


class TestContactsDocReposition:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CONTACT_DOC.read_text(encoding="utf-8")

    def test_badge_starter_autonome_avance(self):
        # L'en-tête (badge) présente Contacts comme starter autonome
        # avancé (plus de « Palier 12 », plus de « Niveau 1 débutant »).
        assert "Palier 12" not in self.content, (
            "Le badge Contacts ne doit plus afficher « Palier 12 » : "
            "Contacts est un starter autonome avancé, pas un palier."
        )
        assert "autonome avancé" in self.content, (
            "Le badge Contacts doit présenter un « starter autonome "
            "avancé »."
        )

    def test_mention_synthese_avancee(self):
        assert "synthèse avancée" in self.content.lower(), (
            "La page Contacts doit présenter le starter comme une "
            "« synthèse avancée »."
        )

    @pytest.mark.parametrize("prereq_marker", [
        "request.param",
        "BaseController.render",
        "request.route_param",
        "CSRF",
        "fetch_one",
    ])
    def test_prerequis_pedagogiques_listes(self, prereq_marker: str):
        # La page doit lister explicitement les prérequis tirés des
        # paliers 1 à 8.
        assert prereq_marker in self.content, (
            f"La page Contacts doit lister `{prereq_marker}` parmi "
            "les prérequis pédagogiques."
        )

    @pytest.mark.parametrize("forbidden_label", [
        "Niveau 1",
        "Premier parcours Forge",
        "Débutant Forge",
        "point d'entrée officiel de Forge",
    ])
    def test_anciennes_etiquettes_debutant_retirees(self, forbidden_label: str):
        # Ces étiquettes positionnaient Contacts comme starter
        # débutant ; le repositionnement les retire.
        assert forbidden_label not in self.content, (
            f"L'étiquette « {forbidden_label} » doit être retirée de "
            "la page Contacts (positionnement débutant trompeur)."
        )

    def test_redirection_bonjour_forge_pour_premier_contact(self):
        # La page recommande explicitement Bonjour Forge pour le
        # premier contact, pas Contacts CRUD.
        assert "Bonjour Forge" in self.content, (
            "La page Contacts doit pointer vers Bonjour Forge pour le "
            "premier contact avec Forge."
        )
        assert (
            "../welcome/welcome.md" in self.content
            or "welcome/welcome.md" in self.content
        ), (
            "La page Contacts doit lier explicitement vers la doc "
            "`welcome/welcome.md`."
        )


# ── Catalogue starters/index.md — section Starter 1 ───────────────────────────


class TestStartersCatalogContactsSection:

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = STARTERS_INDEX.read_text(encoding="utf-8")
        self.section = _extract_contacts_section(self.content)

    def test_section_contacts_repositionnee_avance(self):
        assert self.section, "Section « Contacts » introuvable."
        assert "avancé" in self.section.lower(), (
            "La section catalogue de Contacts doit présenter le starter "
            "comme « autonome avancé »."
        )

    @pytest.mark.parametrize("forbidden_in_section", [
        "idéal pour découvrir Forge",
        "premier parcours Forge",
    ])
    def test_section_contacts_sans_etiquette_debutant(self, forbidden_in_section: str):
        assert forbidden_in_section not in self.section, (
            f"« {forbidden_in_section} » doit être retiré de la "
            "section catalogue de Contacts CRUD."
        )


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_lists_ticket_as_delivered():
    text = ROADMAP.read_text(encoding="utf-8")
    assert "STARTER-CONTACTS-CRUD-REPOSITION-001" in text, (
        "La roadmap doit mentionner STARTER-CONTACTS-CRUD-REPOSITION-001."
    )
    lines = [
        line for line in text.splitlines()
        if "STARTER-CONTACTS-CRUD-REPOSITION-001" in line
    ]
    assert any("**livré**" in line for line in lines), (
        "STARTER-CONTACTS-CRUD-REPOSITION-001 doit être marqué « livré »."
    )
