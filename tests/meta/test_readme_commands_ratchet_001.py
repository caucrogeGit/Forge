"""`META-README-COMMANDS-RATCHET-001` — le README d'un opt-in ne ment pas sur ses commandes.

Le README de `forge-mvc-admin` annonçait que « les filtres de liste et les
actions en masse restent à venir » alors que les filtres étaient livrés. Un
README qui décrit un état antérieur à son code est pire qu'un README absent :
il fait chercher ailleurs ce qui est déjà là, et personne ne le relit puisqu'il
a l'air à jour.

Ce garde-fou ne peut pas vérifier une phrase de prose. Il vérifie ce qui est
vérifiable, et qui dérive de la même façon : **les commandes**.

Chaque opt-in déclare ses commandes dans `COMMANDS`, table lue par le cœur
(ADR-059). Son README en annonce dans un tableau. Les deux doivent s'accorder.

## Ce que le garde-fou refuse, et ce qu'il tolère

Il **refuse** qu'un README annonce une commande que `COMMANDS` ne déclare pas :
c'est la promesse d'une commande qui n'existe pas, et l'utilisateur la tape
avant de comprendre.

Il **tolère** qu'une commande de `COMMANDS` ne figure pas au README : un README
n'est pas une référence exhaustive, et l'aide riche du CLI porte déjà ce
contrat. Exiger l'inverse transformerait chaque README en catalogue.
"""
from __future__ import annotations

import importlib
import re
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PACKAGES = PROJECT_ROOT / "packages"

#: Une commande Forge citée dans un README, `forge <espace>:<verbe>`.
_COMMANDE = re.compile(r"`forge ([a-z][a-z0-9_-]*:[a-z][a-z0-9_:-]*)`")


def _optins_avec_commandes() -> "list[tuple[str, Path, dict[str, Any]]]":
    """Opt-ins déclarant un module `commands`, avec leur README."""
    trouves: list[tuple[str, Path, dict[str, Any]]] = []
    for dossier in sorted(PACKAGES.iterdir()):
        if not dossier.is_dir():
            continue
        readme = dossier / "README.md"
        if not readme.is_file():
            continue
        module_dir = dossier / dossier.name.replace("-", "_")
        if not (module_dir / "commands.py").is_file():
            continue
        try:
            module = importlib.import_module(f"{module_dir.name}.commands")
        except ImportError:
            continue
        commandes = getattr(module, "COMMANDS", None)
        if isinstance(commandes, dict):
            trouves.append((dossier.name, readme, commandes))
    return trouves


_OPTINS = _optins_avec_commandes()


def test_au_moins_un_optin_est_examine() -> None:
    """Un garde-fou sans entrée est un garde-fou qui ne garde rien.

    Il est déjà arrivé qu'un détecteur passe au vert parce qu'il ne trouvait
    plus ses fichiers.
    """
    assert _OPTINS, "aucun opt-in avec COMMANDS n'a été trouvé"


@pytest.mark.parametrize(
    "paquet,readme,commandes",
    _OPTINS,
    ids=[nom for nom, _, _ in _OPTINS],
)
def test_le_readme_n_annonce_aucune_commande_absente(
    paquet: str, readme: Path, commandes: "dict[str, Any]"
) -> None:
    """Toute commande citée par le README existe dans `COMMANDS`.

    L'espace de noms est comparé, pas seulement le nom exact : un README peut
    citer `forge migration:apply`, commande du cœur, à côté de ses propres
    commandes. Seules celles qui portent l'espace de noms de l'opt-in sont
    exigées de lui.
    """
    texte = readme.read_text(encoding="utf-8")
    citees = set(_COMMANDE.findall(texte))
    if not citees:
        pytest.skip(f"{paquet} ne cite aucune commande dans son README")

    espaces = {nom.split(":", 1)[0] for nom in commandes}
    siennes = {c for c in citees if c.split(":", 1)[0] in espaces}
    manquantes = sorted(siennes - set(commandes))

    assert not manquantes, (
        f"{paquet} : son README annonce une ou plusieurs commandes que "
        f"COMMANDS ne déclare pas : {', '.join(manquantes)}.\n"
        f"COMMANDS déclare : {', '.join(sorted(commandes)) or '<aucune>'}.\n"
        "Un README qui promet une commande inexistante la fait taper avant "
        "d'être compris."
    )


@pytest.mark.parametrize(
    "paquet,readme,commandes",
    _OPTINS,
    ids=[nom for nom, _, _ in _OPTINS],
)
def test_le_readme_n_annonce_rien_comme_a_venir_qui_existe(
    paquet: str, readme: Path, commandes: "dict[str, Any]"
) -> None:
    """Aucune commande déclarée n'est annoncée « à venir ».

    C'est la forme exacte de la dérive qui a motivé le ticket : le README de
    `forge-mvc-admin` annonçait comme à venir des fonctions déjà livrées.

    Le contrôle est volontairement étroit, une phrase de prose n'étant pas
    vérifiable en général : il ne regarde que les lignes qui citent une
    commande **et** un mot d'attente.
    """
    attente = re.compile(r"\b(à venir|a venir|pas encore|prévu|prevu|bientôt|bientot)\b", re.IGNORECASE)
    fautes: list[str] = []
    for numero, ligne in enumerate(readme.read_text(encoding="utf-8").splitlines(), 1):
        if not attente.search(ligne):
            continue
        for nom in _COMMANDE.findall(ligne):
            if nom in commandes:
                fautes.append(f"ligne {numero} : {nom}")

    assert not fautes, (
        f"{paquet} : son README annonce comme à venir une commande déjà "
        f"déclarée dans COMMANDS.\n  " + "\n  ".join(fautes)
    )
