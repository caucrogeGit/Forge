"""Garde-fou LANDING-BETA12-HIGHLIGHTS-001.

Vérifie que la landing canonique (`mvc/views/landing/index.html`) met en
avant les apports de Forge `1.0.0-beta.12` : bloc Forge IoT, opt-ins
explicites, installation core-autonome / IoT-opt-in, et preuve qualité
(« suite complète à 0 échec »).

Contrôle aussi que :
- `docs/index.html` (généré par `forge sync:landing`) est synchronisé ;
- les pages doc cibles (IoT + opt-ins + audits) existent ;
- la landing ne présente plus `1.0.0-beta.11` comme version active ;
- la roadmap mentionne le ticket.

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
# Contenu beta.12 attendu dans la landing
# ---------------------------------------------------------------------------

HIGHLIGHTS = [
    "1.0.0-beta.12",
    "forge-mvc-iot",
    "Forge IoT",
    "MQTT",
    "Mosquitto",
    "iot_events",
    "forge iot:doctor",
    "forge iot:listen",
    "forge iot:simulate",
    "optins/",
    "forge opt-in:enable iot",
    "forge opt-in:list",
    "welcome-optin-iot",
    "0 échec",
]


class TestHighlightsPresent:
    @pytest.mark.parametrize("needle", HIGHLIGHTS)
    def test_landing_mentions(self, needle: str):
        assert needle in _src(), (
            f"La landing doit mettre en avant {needle!r} (beta.12)."
        )

    def test_section_beta12_presente(self):
        text = _src()
        assert 'id="beta12"' in text, (
            "Une section dédiée aux nouveautés beta.12 (id='beta12') est attendue."
        )

    def test_core_reste_autonome(self):
        """Le core doit rester présenté comme installable seul, IoT en opt-in."""
        normalized = " ".join(_src().split())
        assert "pip install --pre forge-mvc" in normalized
        assert "pip install --pre forge-mvc-iot" in normalized
        assert "autonome" in normalized

    def test_pas_de_decouverte_magique(self):
        normalized = " ".join(_src().split()).lower()
        assert "pas de découverte magique" in normalized


# ---------------------------------------------------------------------------
# Liens vers la doc — cibles existantes
# ---------------------------------------------------------------------------

IOT_LINKS = [
    ("iot/architecture/", "iot/architecture.md"),
    ("iot/mosquitto-local/", "iot/mosquitto-local.md"),
    ("iot/doctor/", "iot/doctor.md"),
    ("iot/listen-command/", "iot/listen-command.md"),
    ("iot/simulator/", "iot/simulator.md"),
    ("iot/esp32-example/", "iot/esp32-example.md"),
    ("iot/bts-ciel/", "iot/bts-ciel.md"),
]

OPTINS_LINKS = [
    ("architecture/optins-project-structure/", "architecture/optins-project-structure.md"),
    ("architecture/optins-cli-enable-audit/", "architecture/optins-cli-enable-audit.md"),
    ("reference/cli-commands/", "reference/cli-commands.md"),
    ("starters/optin-iot/welcome-optin-iot/", "starters/optin-iot/welcome-optin-iot.md"),
]

AUDIT_LINKS = [
    ("history/audits/audit-pre-release-beta12/", "history/audits/audit-pre-release-beta12.md"),
    ("history/audits/audit-beta12-post-publish/", "history/audits/audit-beta12-post-publish.md"),
]

ALL_LINKS = IOT_LINKS + OPTINS_LINKS + AUDIT_LINKS


class TestDocLinks:
    @pytest.mark.parametrize("href_fragment,target", ALL_LINKS, ids=lambda v: str(v))
    def test_lien_present_et_cible_existe(self, href_fragment: str, target: str):
        # Le lien (URL absolue forgemvc.com/docs/forge/...) doit figurer.
        assert href_fragment in _src(), (
            f"Lien manquant dans la landing : .../{href_fragment}"
        )
        # La page doc canonique doit exister (pas de lien cassé).
        assert (DOCS / target).exists(), (
            f"Page doc cible absente : docs/{target}"
        )


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

    def test_docs_index_reflete_beta12(self):
        docs = DOCS_LANDING.read_text(encoding="utf-8")
        assert 'id="beta12"' in docs
        assert "forge-mvc-iot" in docs


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
