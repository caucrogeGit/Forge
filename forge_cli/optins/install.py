"""Commande ``forge opt-in:install <name>`` — OPTIN-CLI-VERBS-001 (ADR-016, 3a).

Affiche la commande d'installation du package d'un opt-in officiel. **N'exécute
rien** et ne side-effecte pas l'environnement Python : ``install`` *affiche* la
commande à lancer (``pip`` en venv, ``pipx inject`` en installation pipx),
comme ``forge update`` en mode pipx. Le choix « afficher plutôt qu'exécuter »
est acté pour le ticket 3 (présence du package = geste explicite de
l'utilisateur).
"""
from __future__ import annotations

import os
import sys

from forge_cli.optins.catalog import OFFICIAL_OPTINS, optin_names


def _is_pipx_install() -> bool:
    """Détecte si Forge tourne depuis un venv pipx (cf. forge_cli/update.py)."""
    norm = os.path.realpath(sys.executable).replace("\\", "/")
    return "/pipx/venvs/" in norm


def _usage() -> str:
    return (
        "Usage : forge opt-in:install <name>\n"
        f"Opt-ins officiels : {', '.join(optin_names())}"
    )


def main(args: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if args is None else args)

    if argv[:1] in (["-h"], ["--help"]):
        print(_usage())
        return 0

    if not argv:
        print(_usage(), file=sys.stderr)
        return 2

    name = argv[0]
    optin = OFFICIAL_OPTINS.get(name)
    if optin is None:
        print(f"[ERREUR] opt-in inconnu : {name!r}", file=sys.stderr)
        print(_usage(), file=sys.stderr)
        return 2

    dist = optin.package_dist
    print(f"Opt-in « {name} » — {optin.summary}")
    print(f"Package : {dist}")
    print()
    if _is_pipx_install():
        print("Installation (environnement pipx) — injecte la brique dans le venv de Forge :")
        print(f'  pipx inject forge-mvc {dist} --pip-args="--pre"')
    else:
        print("Installation (environnement courant) :")
        print(f"  {sys.executable} -m pip install --pre {dist}")
    print()
    print("Puis branche l'opt-in dans le projet :")
    print(f"  forge opt-in:enable {name}")
    return 0
