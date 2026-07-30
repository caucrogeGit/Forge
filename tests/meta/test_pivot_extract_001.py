"""PIVOT-EXTRACT-001, devenu test d'absence : le pivot a été absorbé (ADR-070).

Ce fichier éprouvait l'opt-in `forge-mvc-pivot`, extrait du cœur par l'ADR-021.
L'ADR-070 a ensuite absorbé ce paquet dans `forge-mvc-entities`, et le dossier
a disparu de `packages/`. Le fichier a survécu en l'état, ouvert par un
`importorskip` sur un module qui n'existe plus : cent trente-sept lignes de test
qui se sautaient à chaque exécution, donc ne prouvaient plus rien tout en
donnant l'apparence d'une couverture.

La convention du dépôt veut qu'une suppression laisse un test d'**absence**,
pas un test endormi. C'est ce qu'il devient : le pivot ne doit plus exister
comme paquet, ni comme module importable, et sa capacité doit vivre là où
l'ADR-070 l'a mise.

Le sort de la distribution restée sur PyPI est traité par
`test_pkg_orphan_yank_001.py`.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def test_le_paquet_pivot_n_est_plus_au_depot() -> None:
    assert not (PROJECT_ROOT / "packages" / "forge-mvc-pivot").exists()


def test_le_module_pivot_n_est_plus_importable() -> None:
    """Un `importorskip` sur ce nom rendrait tout un fichier silencieux."""
    assert importlib.util.find_spec("forge_mvc_pivot") is None


def test_la_capacite_pivot_vit_dans_le_moteur_d_entites() -> None:
    """L'ADR-070 ne supprime pas la fonction, il la déplace."""
    entities = PROJECT_ROOT / "packages" / "forge-mvc-entities"

    assert entities.is_dir()
    sources = " ".join(p.name for p in entities.rglob("*.py"))
    assert "pivot" in sources.lower(), (
        "aucun module de pivot dans forge-mvc-entities : l'absorption n'a pas eu lieu"
    )


def test_aucun_test_du_depot_ne_dort_sur_ce_nom() -> None:
    """Le défaut à ne pas reproduire : un fichier entier sauté sans le dire."""
    fautes: "list[str]" = []
    motif = 'importorskip("forge_mvc' + '_pivot")'  # coupé : sinon l'audit se détecte
    for fichier in PROJECT_ROOT.rglob("tests/**/test_*.py"):
        if "build/" in fichier.as_posix() or fichier == Path(__file__):
            continue
        texte = fichier.read_text(encoding="utf-8")
        if motif in texte:
            fautes.append(str(fichier.relative_to(PROJECT_ROOT)))

    assert not fautes, (
        "ces fichiers s'ouvrent sur un module absorbé, donc se sautent en "
        "entier : " + ", ".join(fautes)
    )
