# pyright: strict
"""forge-mvc-fixtures — opt-in de données de démo et de test (ADR-074).

Opt-in CLI-only : ce paquet ajoutera les commandes ``forge fixtures:load`` et
``forge fixtures:purge`` (données de démonstration et de test **rejouables** et
**cadrées par environnement**). Il n'expose aucune API runtime ; une application
ne l'importe jamais à l'exécution.

Frontière avec la migration de seed (ADR-074, principe 11) : le référentiel
**permanent** reste une migration appliquée par ``forge migration:apply`` ; les
données de démo/test rejouables relèvent de cet opt-in.

Ce module est le **scaffold** du paquet (premier ticket). Les commandes sont
livrées aux tickets suivants, avec un contrat complet (charte principe 10 : pas
d'API publique à moitié faite). La table ``commands.COMMANDS`` est donc vide
pour l'instant.
"""
from __future__ import annotations

__version__ = "1.0.0rc2"

__all__: list[str] = []
