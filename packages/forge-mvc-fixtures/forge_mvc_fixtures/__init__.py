# pyright: strict
"""forge-mvc-fixtures — opt-in de données de démo et de test (ADR-074).

Opt-in CLI-only : ce paquet ajoutera les commandes ``forge fixtures:load`` et
``forge fixtures:purge`` (données de démonstration et de test **rejouables** et
**cadrées par environnement**). Il n'expose aucune API runtime ; une application
ne l'importe jamais à l'exécution.

Frontière avec la migration de seed (ADR-074, principe 11) : le référentiel
**permanent** reste une migration appliquée par ``forge migration:apply`` ; les
données de démo/test rejouables relèvent de cet opt-in.

API publique : la classe de base ``Factory`` (ADR-076), importée par le code de
factory de l'utilisateur (``mvc/fixtures/factories/``) et exécutée par
``fixtures:generate`` pour produire des ``.sql`` relus. Ce n'est pas une API de
runtime : l'application ne l'importe jamais dans le chemin d'une requête.
"""
from __future__ import annotations

from forge_mvc_fixtures.factory import (
    Factory,
    FactoryError,
    Fixture,
    FixtureReference,
)

__version__ = "1.0.0rc3"

__all__ = ["Factory", "FactoryError", "Fixture", "FixtureReference"]
