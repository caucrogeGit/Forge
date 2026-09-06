"""WELCOME-CHAINES-DERIVEES-001 : chaque palier mène au suivant, partout.

Chaque paquet portait son propre garde-fou de chaîne, et chacun **figeait la
liste des pages** plutôt que la propriété. Ajouter un palier légitime les
faisait tomber, quatre fois de suite sur quatre paquets, alors que la chaîne
était intacte à chaque fois.

Ce contrôle-ci dérive la chaîne du `nav` de chaque paquet, qui fait autorité :
c'est l'ordre que le lecteur voit dans le menu. Il vérifie une seule propriété,
et elle vaut pour tous les parcours à la fois.

Un parcours sans cul-de-sac, c'est un lecteur qui sait toujours où aller.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
NIVEAUX = ("debutant", "intermediaire", "avance")
PAGE = re.compile(r"(welcome/(debutant|intermediaire|avance)/([\w-]+\.md))\s*$")


def _paquets() -> "list[str]":
    """Paquets qui portent un parcours d'accueil à niveaux."""
    racine = PROJECT_ROOT / "packages"
    return sorted(
        d.name
        for d in racine.iterdir()
        if (d / "mkdocs.yml").is_file() and (d / "docs" / "welcome").is_dir()
    )


def _nav_par_niveau(paquet: str) -> "dict[str, list[str]]":
    config = PROJECT_ROOT / "packages" / paquet / "mkdocs.yml"
    niveaux: "dict[str, list[str]]" = {}
    for ligne in config.read_text(encoding="utf-8").splitlines():
        trouve = PAGE.search(ligne)
        if trouve:
            niveaux.setdefault(trouve.group(2), []).append(trouve.group(3))
    return niveaux


def _cas() -> "list[tuple[str, str]]":
    return [(p, n) for p in _paquets() for n in NIVEAUX if _nav_par_niveau(p).get(n)]


@pytest.mark.parametrize("paquet,niveau", _cas(), ids=lambda v: str(v))
def test_chaque_palier_mene_au_suivant(paquet: str, niveau: str) -> None:
    """Le dernier palier mène au bilan ; chaque autre mène à son suivant."""
    dossier = PROJECT_ROOT / "packages" / paquet / "docs" / "welcome" / niveau
    pages = _nav_par_niveau(paquet)[niveau]

    assert pages[-1] == "bilan.md", (
        f"{paquet}/{niveau} ne finit pas par son bilan : {pages[-1]}")

    for courante, suivante in zip(pages, pages[1:]):
        texte = (dossier / courante).read_text(encoding="utf-8")
        assert f"({suivante})" in texte, (
            f"{paquet}/{niveau}/{courante} ne mène pas à {suivante}")


@pytest.mark.parametrize("paquet", _paquets())
def test_chaque_page_du_nav_existe(paquet: str) -> None:
    """Une entrée de menu sans fichier est un lien mort dans le site."""
    racine = PROJECT_ROOT / "packages" / paquet / "docs"
    for niveau, pages in _nav_par_niveau(paquet).items():
        for page in pages:
            chemin = racine / "welcome" / niveau / page
            assert chemin.is_file(), f"{paquet} : {chemin.name} est au nav, absent du disque"
