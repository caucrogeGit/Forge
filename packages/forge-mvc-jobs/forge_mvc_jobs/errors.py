# pyright: strict
"""Erreurs du paquet forge-mvc-jobs."""
from __future__ import annotations


class JobError(ValueError):
    """Entrée invalide pour une tâche de fond.

    Levée par exemple quand le nom de tâche est vide ou que la charge utile
    n'est pas sérialisable en JSON. Hérite de ``ValueError``.
    """
