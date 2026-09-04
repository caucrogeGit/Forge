# pyright: strict
"""Ressources front d'un projet engendré (`FORGE-NEW-NO-NODE-DEFAULT-001`).

`forge new` lançait `npm install` puis `npm run build:css` à chaque création.

Mesuré : **deux minutes sur cent quarante-quatre**, pour produire un
`static/tailwind.css` identique au bit près à celui que le squelette versionne.
Le rebâtir à la création ne produisait donc rien, et exigeait pourtant une
chaîne Node complète, `@parcel/watcher` compilé depuis ses sources compris.

Le fichier livré ne peut plus dériver en silence : un garde-fou refuse qu'il
manque une classe utilisée par les gabarits du squelette
(`SKELETON-TAILWIND-CSS-STALE-001`). C'était la condition pour cesser de le
reconstruire.

Node reste à un appel de distance, et l'annonce le dit plutôt que de laisser
deviner : `--with-node` à la création, ou `npm install && npm run build:css`
plus tard. Le squelette continue de livrer `package.json` et
`static/src/input.css` : rien n'est retiré, seule la dépense l'est.

Ce module vit hors de `forge.py`, que l'ADR-059 veut mince et dont un garde-fou
plafonne la longueur.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Callable, Protocol


class _Executeur(Protocol):
    """Lanceur de sous-processus fourni par l'appelant.

    La signature reproduit celle de `forge._run`, paramètres nommables compris :
    un protocole qui exigerait `cwd` en mot-clé seul refuserait la fonction
    réelle, et le typage aurait alors décrit une autre API que celle qui est
    appelée.
    """

    def __call__(
        self,
        args: "list[str]",
        cwd: "str | None" = ...,
        capture: bool = ...,
        check: bool = ...,
    ) -> "subprocess.CompletedProcess[str]": ...


def annoncer_css_livre(afficher_etape: "Callable[[str], None]") -> None:
    """Dit que le CSS est présent, et comment le rebâtir."""
    afficher_etape("CSS Tailwind : le squelette livre static/tailwind.css, déjà à jour.")
    print("    Après modification des gabarits, le rebâtir avec :")
    print("      npm install && npm run build:css")
    print("    Ou dès la création : forge new <nom> --with-node")


def installer_node(
    dest: str, afficher_etape: "Callable[[str], None]", executer: _Executeur
) -> "list[str]":
    """Installe les dépendances Node et recompile le CSS. Rend les avertissements.

    Appelée seulement sur `--with-node` : la dépense est choisie, pas subie.
    """
    avertissements: "list[str]" = []
    if not os.path.exists(os.path.join(dest, "package.json")):
        return avertissements

    if shutil.which("npm") is None:
        avertissements.append(
            "Node.js / npm absent — le CSS livré reste en place ; relancer "
            "'npm install && npm run build:css' après avoir installé Node")
        return avertissements

    afficher_etape("Installation des dépendances Node.js...")
    executer(["npm", "install"], cwd=dest, check=True)

    afficher_etape("Compilation du CSS Tailwind...")
    resultat = executer(["npm", "run", "build:css"], cwd=dest, capture=True)
    if resultat.returncode != 0:
        avertissements.append(
            "build:css a échoué — relancer 'npm run build:css' après avoir "
            "configuré Tailwind")
    return avertissements
