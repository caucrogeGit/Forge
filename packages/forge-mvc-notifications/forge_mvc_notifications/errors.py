# pyright: strict
"""Erreurs du paquet forge-mvc-notifications."""
from __future__ import annotations


class NotificationError(ValueError):
    """Entrée invalide pour une notification applicative.

    Levée par exemple quand le destinataire ou le message est vide, ou quand les
    données ne sont pas sérialisables en JSON. Hérite de ``ValueError``.
    """
