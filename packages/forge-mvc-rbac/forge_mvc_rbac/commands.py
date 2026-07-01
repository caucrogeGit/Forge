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

COMMANDS: dict[str, dict[str, str | bool]] = {
    "rbac:validate": _RBAC,
    "rbac:audit": _RBAC,
}
