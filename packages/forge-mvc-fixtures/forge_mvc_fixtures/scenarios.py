# pyright: strict
"""Jeux de fixtures nommés (`FIXTURES-SCENARIOS-001`).

`mvc/fixtures/` était plat : tous les fichiers se chargeaient ensemble, et un
projet qui voulait un jeu de démonstration riche **et** un jeu de test minimal
devait commenter des fichiers ou les déplacer à la main entre deux exécutions.

## La convention

    mvc/fixtures/
        01_roles.sql            <- jeu commun, toujours chargé
        demo/
            10_articles.sql     <- forge fixtures:load --scenario demo
        test/
            10_articles.sql     <- forge fixtures:load --scenario test

Le jeu commun est chargé **d'abord**, puis celui du scénario : un scénario
complète une base partagée au lieu de la réécrire. Sans `--scenario`, seul le
jeu commun est chargé, ce qui est le comportement d'avant ce ticket.

## Trois noms suggérés, aucun imposé

`demo`, `test` et `minimal` couvrent les besoins courants, et la documentation
les emploie. Ce ne sont que des noms de dossiers : Forge n'en connaît aucun, et
n'en réserve aucun. Imposer une liste fermée obligerait à un ticket pour chaque
projet ayant un quatrième besoin.

## Un nom inconnu est une erreur, jamais un chargement vide

C'est le point qui compte. `--scenario dmo`, faute de frappe pour `demo`,
chargerait zéro fichier et annoncerait un succès : l'exploitant croirait ses
données en place, et chercherait ailleurs pourquoi son application est vide.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "ScenarioError",
    "SUGGESTED_SCENARIOS",
    "ScenarioSelection",
    "fixtures_root",
    "available_scenarios",
    "select_scenario_files",
]

#: Noms employés par la documentation. Aucun n'est réservé ni imposé.
SUGGESTED_SCENARIOS = ("demo", "test", "minimal")

#: Le nom devient un dossier : il doit être un segment de chemin sûr.
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


class ScenarioError(ValueError):
    """Scénario inconnu, ou nom de scénario invalide."""


@dataclass(frozen=True)
class ScenarioSelection:
    """Fichiers retenus, et d'où ils viennent.

    Les deux listes restent distinctes pour que la commande puisse dire ce
    qu'elle charge : « 3 communs, 7 du scénario demo » se vérifie, « 10
    fichiers » ne se vérifie pas.
    """

    common: "tuple[Path, ...]"
    scenario: "tuple[Path, ...]"
    name: "str | None" = None

    @property
    def files(self) -> "tuple[Path, ...]":
        """Tous les fichiers, le jeu commun d'abord."""
        return self.common + self.scenario

    @property
    def is_empty(self) -> bool:
        return not self.files


def fixtures_root(root: Path) -> Path:
    return root / "mvc" / "fixtures"


def available_scenarios(root: Path) -> "tuple[str, ...]":
    """Scénarios présents sur le disque, triés.

    Un sous-dossier ne compte que s'il contient au moins un fichier chargeable :
    un dossier vide, ou qui ne porte que des notes, n'est pas un scénario et le
    proposer ferait croire à un jeu qui n'existe pas.
    """
    base = fixtures_root(root)
    if not base.is_dir():
        return ()
    trouves: list[str] = []
    for enfant in sorted(base.iterdir()):
        if not enfant.is_dir() or enfant.name.startswith((".", "_")):
            continue
        if not _NAME_RE.fullmatch(enfant.name):
            continue
        if any(enfant.glob("*.sql")) or any(enfant.glob("*.py")):
            trouves.append(enfant.name)
    return tuple(trouves)


def select_scenario_files(
    root: Path, name: "str | None" = None, *, pattern: str = "*.sql"
) -> ScenarioSelection:
    """Fichiers à charger, jeu commun puis scénario.

    Args:
        name: scénario demandé. `None` ne charge que le jeu commun, comportement
            d'avant `FIXTURES-SCENARIOS-001`.
        pattern: motif des fichiers retenus, `*.sql` ou `*.py`.

    Raises:
        ScenarioError: nom invalide, ou scénario absent du projet. Charger zéro
            fichier en annonçant un succès ferait croire les données en place.
    """
    base = fixtures_root(root)
    communs = tuple(sorted(base.glob(pattern), key=lambda p: p.name)) if base.is_dir() else ()

    if name is None:
        return ScenarioSelection(communs, (), None)

    demande = name.strip().lower()
    if not _NAME_RE.fullmatch(demande):
        raise ScenarioError(
            f"nom de scénario invalide : {name!r}. Le nom devient un dossier, "
            "il doit être en minuscules, chiffres, tiret ou souligné."
        )

    dossier = base / demande
    if not dossier.is_dir():
        connus = available_scenarios(root)
        detail = (
            f" Scénarios présents : {', '.join(connus)}."
            if connus
            else " Aucun sous-dossier de scénario dans mvc/fixtures/."
        )
        raise ScenarioError(f"scénario inconnu : {demande!r}.{detail}")

    fichiers = tuple(sorted(dossier.glob(pattern), key=lambda p: p.name))
    if not fichiers and pattern == "*.sql" and not any(dossier.glob("*.py")):
        raise ScenarioError(
            f"le scénario {demande!r} ne contient aucun fichier chargeable. "
            "Un chargement vide annoncé comme un succès ferait croire les "
            "données en place."
        )
    return ScenarioSelection(communs, fichiers, demande)
