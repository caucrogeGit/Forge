# pyright: strict
"""Commandes CLI de forge-mvc-deploy, découvertes par le cœur (ADR-059).

Table déclarative légère exposée via l'entry point ``forge_mvc.commands``. Le
handler ``forge_mvc_deploy.cli.deploy:main`` dispatche lui-même sur la
sous-commande, il reçoit donc les arguments complets (``full``).
"""
from __future__ import annotations

_DEPLOY: dict[str, str | bool] = {
    "module": "forge_mvc_deploy.cli.deploy",
    "full": True,
    "exit_rc": False,
}

COMMANDS: dict[str, dict[str, str | bool]] = {
    "deploy:init": _DEPLOY,
    "deploy:check": _DEPLOY,
}
