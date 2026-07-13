"""Garde-fou AGENTS-SEED-ADR-001 (ADR-047).

Les ADR d'amorçage existent, actent une décision réelle (adoption de Forge ;
style de documentation), respectent le format ADR (Statut, Date, Contexte,
Décision, Conséquences, Alternatives), et acceptent une date injectée à
l'écriture.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.meta

from cli.agents import render_seed_adr, render_seed_adr_doc_style


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


# ── ADR-002 : style de documentation ─────────────────────────────────────────

def test_doc_style_titre_et_format():
    text = render_seed_adr_doc_style()
    assert text.startswith("# ADR-002 : Style et rédaction de la documentation")
    for section in ("## Statut", "## Date", "## Contexte", "## Décision",
                    "## Conséquences", "## Alternatives écartées"):
        assert section in text, f"section ADR manquante : {section}"


@pytest.mark.parametrize(
    "needle",
    [
        "Une phrase par ligne",
        "tiret cadratin",
        "espaces insécables",
        "guillemets français",
        "français",
        "build strict",
    ],
)
def test_doc_style_contenu_cle(needle: str):
    assert needle in render_seed_adr_doc_style(), f"l'ADR-002 doit mentionner {needle!r}"


def test_doc_style_respecte_ses_propres_regles():
    text = render_seed_adr_doc_style(date="2026-07-13")
    # L'ADR qui interdit le tiret cadratin ne doit pas en contenir.
    assert "—" not in text
    assert "2026-07-13" in text


def test_doc_style_date_injectable():
    assert "2026-06-24" in render_seed_adr_doc_style(date="2026-06-24")
    assert "AAAA-MM-JJ" in render_seed_adr_doc_style()
