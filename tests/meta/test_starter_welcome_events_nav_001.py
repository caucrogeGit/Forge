"""Tests documentaires — STARTER-WELCOME-EVENTS-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-events`
(parcours cœur, registre d'événements applicatif) : chaînage préambule →
registre → câblage → cas réel → angles morts → bilan, et absence de
commande de création de projet.

Verrouille aussi les invariants **doctrinaux** du parcours, qui sont sa
raison d'être : le parcours construit du code applicatif (`mvc/events/`),
pas un opt-in Forge ; il présente le décorateur `@events.on` comme un
contre-exemple refusé et non comme une recommandation ; il renvoie à
l'ADR-052 qui porte la décision ; et il maintient la distinction
« les événements découplent le code, les jobs découplent le temps ».

Couvre enfin le guide de doctrine `docs/features/evenements.md`
(DOCS-EVENTS-DOCTRINE-001) et son appariement réciproque avec le
parcours, sur le modèle du couple guide/parcours de welcome-outils.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
EVENTS = PROJECT_ROOT / "docs" / "starters" / "welcome-events"
GUIDE = PROJECT_ROOT / "docs" / "features" / "evenements.md"

PAGES = (
    "installation.md",
    "registre.md",
    "cablage.md",
    "cas-reel.md",
    "angles-morts.md",
    "bilan.md",
)

CHAIN = (
    ("installation.md", "(registre.md)"),
    ("registre.md", "(cablage.md)"),
    ("cablage.md", "(cas-reel.md)"),
    ("cas-reel.md", "(angles-morts.md)"),
    ("angles-morts.md", "(bilan.md)"),
)

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _read(page: str) -> str:
    return (EVENTS / page).read_text(encoding="utf-8")


def _has(page: str, needle: str) -> bool:
    return needle in _read(page)


@pytest.mark.parametrize("name", PAGES)
def test_pages_present(name: str):
    assert (EVENTS / name).is_file(), f"{name} manquant dans welcome-events/"


@pytest.mark.parametrize("source,link", CHAIN)
def test_chain(source: str, link: str):
    assert _has(source, link), (
        f"{source} doit pointer vers le palier suivant « {link} »."
    )


def test_parcours_is_application_code_not_an_optin():
    """Le parcours construit `mvc/events/`, du code utilisateur.

    Si un paquet `forge-mvc-events` apparaissait un jour, ce parcours
    devrait être recadré (« maquette d'étude ») avant de continuer à
    faire construire le mécanisme à la main : principe 11, une seule
    façon officielle. Ce test signale la bascule.
    """
    for name in ("registre.md", "cablage.md", "cas-reel.md"):
        assert "mvc/events/" in _read(name), (
            f"{name} doit situer le code dans `mvc/events/` (code applicatif)."
        )
    preambule = _read("installation.md")
    assert "Forge ne fournit aucun système d'événements" in preambule, (
        "Le préambule doit annoncer que Forge ne fournit pas ce mécanisme."
    )
    assert not (PROJECT_ROOT / "packages" / "forge-mvc-events").exists(), (
        "Un paquet forge-mvc-events existe : le parcours welcome-events doit "
        "être recadré (enseigner l'usage du paquet, ou se déclarer maquette "
        "d'étude) sous peine de créer deux façons officielles — principe 11."
    )


# Marqueurs qui qualifient `@events.on` comme motif refusé. Toute page qui
# cite le décorateur doit en porter au moins un : le parcours peut le montrer
# (c'est même nécessaire pour le comparer), jamais le proposer.
REFUSAL_MARKERS = ("Contre-exemple", "Ne l'écrivez pas", "viole le principe", "refuse")


def test_decorator_is_shown_as_counter_example():
    """`@events.on` ne doit apparaître que qualifié comme motif refusé."""
    cablage = _read("cablage.md")
    assert "@events.on" in cablage, (
        "Le palier câblage doit montrer la variante refusée pour la comparer."
    )
    assert "Contre-exemple" in cablage and "Ne l'écrivez pas" in cablage, (
        "Le bloc de code `@events.on` doit être marqué comme contre-exemple."
    )
    for name in PAGES:
        text = _read(name)
        if "@events.on" not in text:
            continue
        assert any(marker in text for marker in REFUSAL_MARKERS), (
            f"{name} cite `@events.on` sans le qualifier de motif refusé "
            f"(marqueurs attendus : {REFUSAL_MARKERS})."
        )


@pytest.mark.parametrize("page", ("cablage.md", "bilan.md"))
def test_links_to_adr_052(page: str):
    assert _has(page, "../../adr/052-optin-strategy.md"), (
        f"{page} doit renvoyer à l'ADR-052 qui porte la décision."
    )


def test_wiring_file_is_the_central_lesson():
    cablage = _read("cablage.md")
    assert "wiring.py" in cablage
    assert "app.py" in cablage, (
        "Le câblage doit être situé dans app.py, comme les middlewares."
    )


def test_events_versus_jobs_distinction_kept():
    """La confusion « événements = asynchrone » est le contresens à éviter."""
    angles = _read("angles-morts.md")
    assert "forge_mvc_jobs" in angles or "forge-mvc-jobs" in angles
    assert "découplent le code" in angles and "découplent le temps" in angles


def test_bilan_states_both_columns():
    bilan = _read("bilan.md")
    assert "Vous avez gagné" in bilan and "Vous avez perdu" in bilan, (
        "Le bilan doit présenter gains ET pertes : c'est la leçon du parcours."
    )


# ── Guide de doctrine (DOCS-EVENTS-DOCTRINE-001) ─────────────────────────────


def test_guide_exists_and_links_parcours():
    assert GUIDE.is_file(), "le guide docs/features/evenements.md doit exister"
    text = GUIDE.read_text(encoding="utf-8")
    assert "../starters/welcome-events/installation.md" in text, (
        "Le guide doit renvoyer au parcours qui construit le registre."
    )


def test_bilan_points_to_guide():
    assert _has("bilan.md", "../../features/evenements.md"), (
        "Le bilan du parcours doit renvoyer au guide de référence."
    )


def test_guide_states_forge_provides_nothing():
    """L'affirmation centrale du guide, celle qu'une refonte ne doit pas diluer."""
    text = GUIDE.read_text(encoding="utf-8")
    assert "Forge ne fournit aucun système d'événements" in text
    assert "../adr/052-optin-strategy.md" in text, (
        "Le guide doit citer l'ADR-052, qui porte la décision."
    )


def test_guide_keeps_events_versus_jobs():
    text = GUIDE.read_text(encoding="utf-8")
    assert "découplent le code" in text and "découplent le temps" in text
    assert "../jobs/reference.md" in text


def test_guide_shows_decorator_only_as_counter_example():
    text = GUIDE.read_text(encoding="utf-8")
    if "@events.on" in text:
        assert any(marker in text for marker in REFUSAL_MARKERS), (
            "Le guide cite `@events.on` sans le qualifier de motif refusé."
        )


@pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
def test_command_absent(forbidden: str):
    for page in EVENTS.rglob("*.md"):
        assert forbidden not in page.read_text(encoding="utf-8"), (
            f"`{forbidden}` ne doit pas apparaître dans {page}."
        )
