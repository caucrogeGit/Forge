"""STATS-GENERIC-EVENTS-001 — Garde-fou : absence des constantes et helpers nommés.

Vérifie que :
- les 6 constantes (PAGE_VIEW, CONTACT_CLICK, …) n'existent plus dans core.stats ;
- is_known_event_name() n'existe plus dans core.stats ;
- _KNOWN_EVENT_NAMES n'existe plus dans core/stats/events.py ;
- les fonctions essentielles restent importables et fonctionnelles.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_stats")

pytestmark = pytest.mark.meta


# ---------------------------------------------------------------------------
# Classe 1 — Constantes absentes de l'API publique
# ---------------------------------------------------------------------------

REMOVED_CONSTANTS = [
    "PAGE_VIEW",
    "CONTACT_CLICK",
    "FORM_SUBMIT",
    "DOWNLOAD_CLICK",
    "EXTERNAL_LINK_CLICK",
    "MEDIA_VIEW",
]


class TestConstantesAbsentes:

    @pytest.mark.parametrize("name", REMOVED_CONSTANTS)
    def test_constante_absente_de_core_stats(self, name):
        import forge_mvc_stats as stats
        assert not hasattr(stats, name), (
            f"core.stats ne doit plus exposer {name!r}"
        )

    @pytest.mark.parametrize("name", REMOVED_CONSTANTS)
    def test_constante_absente_de_events_module(self, name):
        import forge_mvc_stats.events as events
        assert not hasattr(events, name), (
            f"core.stats.events ne doit plus exposer {name!r}"
        )

    @pytest.mark.parametrize("name", REMOVED_CONSTANTS)
    def test_constante_absente_de_all(self, name):
        import forge_mvc_stats as stats
        assert name not in getattr(stats, "__all__", []), (
            f"{name!r} ne doit plus figurer dans core.stats.__all__"
        )


# ---------------------------------------------------------------------------
# Classe 2 — is_known_event_name et _KNOWN_EVENT_NAMES absents
# ---------------------------------------------------------------------------

class TestHelperAbsent:

    def test_is_known_event_name_absent_de_core_stats(self):
        import forge_mvc_stats as stats
        assert not hasattr(stats, "is_known_event_name")

    def test_is_known_event_name_absent_de_events(self):
        import forge_mvc_stats.events as events
        assert not hasattr(events, "is_known_event_name")

    def test_is_known_event_name_absent_de_all(self):
        import forge_mvc_stats as stats
        assert "is_known_event_name" not in getattr(stats, "__all__", [])

    def test_known_event_names_set_absent_du_source(self):
        events_file = Path("packages/forge-mvc-stats/forge_mvc_stats/events.py").read_text()
        assert "_KNOWN_EVENT_NAMES" not in events_file

    def test_source_events_ne_contient_pas_constantes(self):
        events_file = Path("packages/forge-mvc-stats/forge_mvc_stats/events.py").read_text()
        for name in REMOVED_CONSTANTS:
            assert f'{name} = ' not in events_file, (
                f"La constante {name} ne doit plus être définie dans events.py"
            )


# ---------------------------------------------------------------------------
# Classe 3 — API essentielle toujours présente
# ---------------------------------------------------------------------------

class TestApiEssentiellePresente:

    def test_stats_event_importable(self):
        from forge_mvc_stats import StatsEvent
        assert StatsEvent is not None

    def test_stats_event_error_importable(self):
        from forge_mvc_stats import StatsEventError
        assert StatsEventError is not None

    def test_make_event_importable_et_callable(self):
        from forge_mvc_stats import make_event
        assert callable(make_event)

    def test_validate_event_name_importable_et_callable(self):
        from forge_mvc_stats import validate_event_name
        assert callable(validate_event_name)

    def test_normalize_event_name_importable_et_callable(self):
        from forge_mvc_stats import normalize_event_name
        assert callable(normalize_event_name)

    def test_validate_event_importable_et_callable(self):
        from forge_mvc_stats import validate_event
        assert callable(validate_event)


# ---------------------------------------------------------------------------
# Classe 4 — Les noms courants restent valides comme chaînes
# ---------------------------------------------------------------------------

COMMON_EVENT_STRINGS = [
    "page_view",
    "contact_click",
    "form_submit",
    "download_click",
    "external_link_click",
    "media_view",
]


class TestNomsRestentValides:

    @pytest.mark.parametrize("name", COMMON_EVENT_STRINGS)
    def test_nom_valide_comme_chaine(self, name):
        from forge_mvc_stats import validate_event_name
        assert validate_event_name(name) == name

    @pytest.mark.parametrize("name", COMMON_EVENT_STRINGS)
    def test_make_event_accepte_nom_comme_chaine(self, name):
        from forge_mvc_stats import make_event
        e = make_event(name)
        assert e.name == name
