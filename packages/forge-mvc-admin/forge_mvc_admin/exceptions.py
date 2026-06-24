# pyright: strict
"""Exceptions de Forge Admin.

Toutes héritent de `ValueError` (convention des opt-ins Forge), via une base
commune `AdminError` qui permet d'attraper l'ensemble en un seul `except`.
"""
from __future__ import annotations


class AdminError(ValueError):
    """Base de toutes les erreurs Forge Admin."""


class AdminResourceError(AdminError):
    """Contrat de ressource admin invalide."""


class AdminRegistryError(AdminError):
    """Opération invalide sur le registre des ressources admin."""
