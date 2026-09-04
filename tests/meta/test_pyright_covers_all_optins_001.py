"""`PKG-PYRIGHT-FIXTURES-001` — le typage couvre tous les opt-ins.

Le commentaire de `[tool.pyright]` annonce que « le cliquet couvre le cœur,
**tous les opt-ins** et les 4 backends BDD ». Il en couvrait vingt-six sur
vingt-sept : `forge-mvc-fixtures` manquait à `include` comme à `extraPaths`.

Ses fichiers portent pourtant tous `# pyright: strict`. Ils ont donc été écrits
pour être vérifiés, et ne l'étaient pas : trois erreurs s'y sont accumulées sans
qu'un seul contrôle proteste, deux fonctions mortes laissées par le
déplacement de l'ordonnancement vers `ordering.py`, et un type partiellement
inconnu que trois `pyright: ignore` masquaient à moitié.

Un paquet ajouté au dépôt ne s'ajoute pas tout seul à cette liste, et rien ne le
signalait. C'est ce que ce garde-fou refuse.
"""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PACKAGES = PROJECT_ROOT / "packages"


def _config_pyright() -> "dict[str, list[str]]":
    racine = tomllib.loads(
        (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return racine["tool"]["pyright"]


def _paquets() -> "list[str]":
    return sorted(d.name for d in PACKAGES.iterdir()
                  if d.is_dir() and (d / "pyproject.toml").is_file())


_PAQUETS = _paquets()
_CONFIG = _config_pyright()


def test_le_releve_a_des_entrees() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien."""
    assert len(_PAQUETS) > 20, f"{len(_PAQUETS)} paquets trouvés"
    assert _CONFIG.get("include"), "la configuration pyright n'est plus lisible"


@pytest.mark.parametrize("paquet", _PAQUETS, ids=_PAQUETS)
def test_le_paquet_est_verifie(paquet: str) -> None:
    """Chaque opt-in figure dans `include`.

    Absent, il n'est pas vérifié du tout, et ses `# pyright: strict` ne
    protègent rien.
    """
    couverts = {chemin.split("/")[1] for chemin in _CONFIG["include"]
                if chemin.startswith("packages/")}

    assert paquet in couverts, (
        f"{paquet} n'est pas dans [tool.pyright].include : ses fichiers ne "
        f"sont vérifiés par personne, `# pyright: strict` compris.")


@pytest.mark.parametrize("paquet", _PAQUETS, ids=_PAQUETS)
def test_le_paquet_est_importable_par_les_autres(paquet: str) -> None:
    """Chaque opt-in figure dans `extraPaths`.

    Pyright ne suit pas les installations éditables PEP 660 : sans son chemin,
    un paquet qui en importe un autre le voit comme inconnu, et le typage
    s'effondre en cascade sur des erreurs qui n'en sont pas.
    """
    assert f"packages/{paquet}" in set(_CONFIG["extraPaths"]), (
        f"packages/{paquet} n'est pas dans [tool.pyright].extraPaths : les "
        f"paquets qui l'importent ne le verront pas.")


def test_le_commentaire_ne_promet_pas_plus_que_la_liste() -> None:
    """Le commentaire disait « tous les opt-ins » pour vingt-six sur vingt-sept.

    Une annonce de complétude qui n'en est pas fait cesser de vérifier : on lit
    la phrase, on conclut que c'est couvert, et on ne compte jamais.
    """
    couverts = {chemin.split("/")[1] for chemin in _CONFIG["include"]
                if chemin.startswith("packages/")}

    assert couverts == set(_PAQUETS), (
        "écart entre les paquets du dépôt et ceux vérifiés :\n"
        f"  absents de include : {', '.join(sorted(set(_PAQUETS) - couverts)) or 'aucun'}\n"
        f"  listés en trop     : {', '.join(sorted(couverts - set(_PAQUETS))) or 'aucun'}")
