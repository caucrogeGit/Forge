"""Garde-fou AGENTS-BRIEFING-TEMPLATE-001 (ADR-047).

Le briefing agent canonique pour les applications Forge existe, vise bien une
**application** (pas le framework), et porte les conventions clés. Distillé : il
ne recopie pas la charte intégrale.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.meta

from cli.agents import render_app_briefing


def _briefing() -> str:
    return render_app_briefing()


def test_briefing_non_vide():
    text = _briefing()
    assert isinstance(text, str) and len(text) > 500


def test_cible_une_application_pas_le_framework():
    text = _briefing().lower()
    assert "application" in text
    assert "tu ne développes pas forge lui-même" in text


@pytest.mark.parametrize(
    "needle",
    [
        "forge make:entity",
        "forge doctor",
        "mvc/routes/__init__.py",
        "core.database.db",
        "CSRF",
        "_base.py",          # règle de préservation du code utilisateur
        "write-if-new",
        "python -m pytest",
        "make check",        # point d'entrée de validation (ADR-063)
        "forgemvc.com",
        "docs/adr/",         # discipline ADR transmise (ADR-047)
        "ADR",
        "ADR-063",           # pointeurs vers les ADR fondateurs (F7, ADR-063)
        "ADR-061",
    ],
)
def test_conventions_cles_presentes(needle: str):
    assert needle in _briefing(), f"le briefing doit mentionner {needle!r}"


def test_reste_distille_pas_de_charte_integrale():
    # Le briefing ne doit pas embarquer la charte complète (gouvernance interne).
    text = _briefing()
    assert "11 principes" not in text
    assert len(text) < 8000, "briefing trop long : il doit rester distillé"
