"""Garde-fou AGENTS-SEED-ADR-001 (ADR-047).

L'ADR-001 d'amorçage existe, acte l'adoption de Forge et de ses conventions,
respecte le format ADR (Statut, Date, Contexte, Décision, Conséquences,
Alternatives), et accepte une date injectée à l'écriture.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.meta

from cli.agents import render_seed_adr


def test_titre_et_format():
    text = render_seed_adr()
    assert text.startswith("# ADR-001 — Adopter Forge")
    for section in ("## Statut", "## Date", "## Contexte", "## Décision",
                    "## Conséquences", "## Alternatives écartées"):
        assert section in text, f"section ADR manquante : {section}"


@pytest.mark.parametrize(
    "needle",
    [
        "contrats JSON",
        "core.database.db",
        "CSRF",
        "discipline ADR",
        "docs/adr/",
        "CLAUDE.md",
        "AGENTS.md",
    ],
)
def test_contenu_cle(needle: str):
    assert needle in render_seed_adr(), f"l'ADR-001 doit mentionner {needle!r}"


def test_date_injectable():
    assert "2026-06-24" in render_seed_adr(date="2026-06-24")
    # sans date : un repère explicite reste pour le développeur
    assert "AAAA-MM-JJ" in render_seed_adr()
