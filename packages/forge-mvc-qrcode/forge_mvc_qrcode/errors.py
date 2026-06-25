# pyright: strict
"""Erreurs du paquet forge-mvc-qrcode."""
from __future__ import annotations


class QrCodeError(ValueError):
    """Entrée invalide pour la génération d'un QR Code.

    Levée par exemple quand le texte à encoder est vide, ou quand un format
    de sortie inconnu est demandé. Hérite de ``ValueError`` : un contrôleur
    peut la rattraper comme une erreur d'entrée ordinaire.
    """
