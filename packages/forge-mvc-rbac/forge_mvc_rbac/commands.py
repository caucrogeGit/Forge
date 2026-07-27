# pyright: strict
"""Commandes CLI de forge-mvc-rbac, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands``. Le
handler ``forge_mvc_rbac.cli:main`` dispatche lui-même sur la sous-commande, il
reçoit donc les arguments complets (``full``).
"""
from __future__ import annotations

_RBAC: dict[str, str | bool] = {
    "module": "forge_mvc_rbac.cli",
    "full": True,
    "exit_rc": False,
}

# `rbac:init` a son propre module : il n'entre pas dans le dispatch interne de
# `forge_mvc_rbac.cli` (contrat/audit), il écrit des migrations comme les autres
# opt-ins adossés à la base (ADR-071). Sans amorçage de config : rendre le DDL
# n'exige que l'identité du backend (entry point, ADR-054), pas les identifiants
# de connexion, et aucune connexion n'est ouverte (charte §7).
COMMANDS: dict[str, dict[str, str | bool]] = {
    "rbac:init": {"module": "forge_mvc_rbac.cli.init"},
    "rbac:validate": _RBAC,
    "rbac:audit": _RBAC,
}
