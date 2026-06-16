"""Garde-fou LANDING-BETA12-HIGHLIGHTS-001 (adapté à la refonte landing).

À l'origine, ce garde-fou vérifiait les apports beta.12 (bloc Forge IoT,
opt-ins explicites, preuve « suite complète à 0 échec », liens profonds
vers la doc IoT et les audits). La refonte visuelle de la landing a
relabelisé la section en « Nouveautés 1.0.0-beta.13 » et simplifié les
panneaux : suppression des liens profonds IoT/audits, de « Mosquitto » et
de la preuve « 0 échec ».

Mise à jour beta.16 : la section est relabelisée « Nouveautés 1.0.0-beta.16 »
(id `beta16`) et met l'accent sur les nouveautés **de la beta.16** : **Parcours
réalisés à la main** (ADR-035, retrait de la génération de starters),
**Déploiement en production** (Gunicorn / WSGI via `deploy:init`), **Cœur encore
allégé** (mail et config upload sortis du noyau, ADR-031/032) et **Comptes de
base de données clarifiés** (provisioning en `forge_admin`, ADR-033/034). Les
nouveautés de beta.15 (i18n, convention de route, squelette dédié) et les
anciennes cartes média sont retirées de la vitrine.

Ce fichier conserve les garde-fous encore valides : présence de la section,
panneaux des nouveautés courantes, core présenté comme autonome,
synchronisation de `docs/index.html`, absence de version beta.11, ticket
roadmap.

Test documentaire : il lit du texte, il n'exécute aucun service.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
LANDING = PROJECT_ROOT / "mvc" / "views" / "landing" / "index.html"
DOCS_LANDING = PROJECT_ROOT / "docs" / "index.html"
DOCS = PROJECT_ROOT / "docs"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _src() -> str:
    return LANDING.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Contenu IoT / opt-ins encore mis en avant après la refonte
# ---------------------------------------------------------------------------

# Refonte « cartes sans code » : la section Nouveautés présente désormais les
# opt-ins par un texte simple (sans commandes CLI ni `iot_events`). Seuls les
# repères conceptuels restent garantis.
HIGHLIGHTS = [
    "Parcours réalisés à la main",
    "Déploiement en production",
    "Cœur encore allégé",
    "Comptes de base de données clarifiés",
]


class TestHighlightsPresent:
    @pytest.mark.parametrize("needle", HIGHLIGHTS)
    def test_landing_mentions(self, needle: str):
        assert needle in _src(), (
            f"La landing doit mettre en avant {needle!r} (IoT / opt-ins)."
        )

    def test_section_nouveautes_presente(self):
        assert 'id="beta16"' in _src(), (
            "Une section dédiée aux nouveautés (id='beta16') est attendue."
        )

    def test_core_reste_autonome(self):
        """Le core doit rester présenté comme autonome (carte Forge i18n)."""
        normalized = " ".join(_src().split())
        assert "autonome" in normalized


# ---------------------------------------------------------------------------
# Synchronisation docs/index.html
# ---------------------------------------------------------------------------


class TestSync:
    def test_docs_index_existe(self):
        assert DOCS_LANDING.exists()

    def test_docs_index_synchronise(self):
        """docs/index.html est généré : préfixe banner + contenu landing."""
        docs = DOCS_LANDING.read_text(encoding="utf-8")
        assert docs.endswith(_src()), (
            "docs/index.html n'est pas synchronisé avec la landing — "
            "lancez `forge sync:landing`."
        )

    def test_docs_index_reflete_section(self):
        docs = DOCS_LANDING.read_text(encoding="utf-8")
        assert 'id="beta16"' in docs
        assert "Parcours réalisés à la main" in docs
        assert "Déploiement en production" in docs


# ---------------------------------------------------------------------------
# Pas de version beta.11 active
# ---------------------------------------------------------------------------


class TestNoStaleVersion:
    def test_pas_de_beta11_active(self):
        assert "1.0.0-beta.11" not in _src(), (
            "La landing ne doit plus afficher 1.0.0-beta.11 comme version."
        )

    def test_pas_de_beta11_dans_docs(self):
        assert "1.0.0-beta.11" not in DOCS_LANDING.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Roadmap
# ---------------------------------------------------------------------------


class TestRoadmap:
    def test_ticket_present(self):
        text = ROADMAP.read_text(encoding="utf-8")
        assert "LANDING-BETA12-HIGHLIGHTS-001" in text

    def test_ticket_livre(self):
        text = ROADMAP.read_text(encoding="utf-8")
        for line in text.splitlines():
            if "LANDING-BETA12-HIGHLIGHTS-001" in line:
                assert "livré" in line.lower(), (
                    f"LANDING-BETA12-HIGHLIGHTS-001 non marqué livré : {line[:80]}"
                )
                return
        pytest.fail("Ligne LANDING-BETA12-HIGHLIGHTS-001 introuvable.")
