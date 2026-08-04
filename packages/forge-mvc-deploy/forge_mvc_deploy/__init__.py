# pyright: strict
"""forge-mvc-deploy — outillage de déploiement opt-in du framework Forge (ADR-053).

Opt-in CLI-only : ce paquet ajoute les commandes ``forge deploy:init`` et
``forge deploy:check`` quand il est installé. Il n'expose aucune API runtime ;
une application ne l'importe jamais à l'exécution.
"""

from __future__ import annotations

from forge_mvc_deploy.cli.deploy import (
    cmd_deploy_check,
    cmd_deploy_init,
    main,
)

__version__ = "1.0.0rc4"

__all__ = [
    "cmd_deploy_init",
    "cmd_deploy_check",
    "main",
]
