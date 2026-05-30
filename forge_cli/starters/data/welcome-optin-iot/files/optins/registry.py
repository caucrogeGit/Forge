"""Registre **explicite** des opt-ins branchés dans ce projet.

Pas de découverte automatique : chaque opt-in actif est importé et appelé
explicitement dans ``register_optins`` ci-dessous. Forge Core ne charge
aucun opt-in tout seul — ajouter un opt-in = ajouter un import + un appel
ici, lisible et sans magie.

Appelé depuis ``mvc/routes.py`` :

    from optins.registry import register_optins

    register_optins(router)
"""

from __future__ import annotations


def register_optins(router) -> None:
    """Branche les routes des opt-ins activés dans ce projet."""
    from optins.iot.routes import register as register_iot

    register_iot(router)
