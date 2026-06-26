# pyright: strict
"""Erreurs du paquet forge-mvc-audit."""
from __future__ import annotations


class AuditError(ValueError):
    """Entrée invalide pour une trace d'audit applicatif.

    Levée par exemple quand l'action est vide. Hérite de ``ValueError`` : un
    appelant peut la rattraper comme une erreur d'entrée ordinaire.
    """
