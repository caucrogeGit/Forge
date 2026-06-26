# pyright: strict
"""Erreurs du paquet forge-mvc-import-export."""
from __future__ import annotations


class CsvImportError(ValueError):
    """Entrée invalide pour un import CSV.

    Levée par exemple quand le CSV est illisible, ou quand une spécification de
    colonne est incohérente. Les erreurs **par ligne** ne lèvent pas cette
    exception : elles sont collectées dans un :class:`ImportReport`. Hérite de
    ``ValueError``.
    """
