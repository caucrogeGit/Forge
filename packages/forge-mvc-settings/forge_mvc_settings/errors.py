# pyright: strict
"""Erreurs du paquet forge-mvc-settings."""
from __future__ import annotations


class SettingsError(ValueError):
    """Entrée invalide pour un paramètre applicatif.

    Levée par exemple quand la clé ne respecte pas le format attendu, ou
    quand la valeur n'est pas d'un type supporté. Hérite de ``ValueError`` :
    un appelant peut la rattraper comme une erreur d'entrée ordinaire.
    """
