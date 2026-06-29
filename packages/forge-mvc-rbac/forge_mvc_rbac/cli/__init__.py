# pyright: strict
"""CLI de l'opt-in RBAC (ADR-056).

Expose les commandes ``rbac:validate`` et ``rbac:audit``, extraites du cœur :
l'opt-in possède désormais son contrat (schéma embarqué) et son outillage de
validation. Le cœur route ``rbac:*`` vers ce point d'entrée si le paquet est
installé (sinon il signale que l'opt-in est absent).
"""
from __future__ import annotations

import sys

from forge_mvc_rbac.cli.rbac_audit import rbac_audit_main
from forge_mvc_rbac.cli.rbac_validate import rbac_validate_main

__all__ = ["main", "rbac_validate_main", "rbac_audit_main"]


def main(args: list[str]) -> None:
    """Point d'entrée des commandes RBAC. ``args`` inclut le nom de commande."""
    command = args[0] if args else ""
    rest = args[1:]
    if command == "rbac:validate":
        rbac_validate_main(rest)
        return
    if command == "rbac:audit":
        rbac_audit_main(rest)
        return
    print(f"Commande RBAC inconnue : «{command}».", file=sys.stderr)
    sys.exit(2)
