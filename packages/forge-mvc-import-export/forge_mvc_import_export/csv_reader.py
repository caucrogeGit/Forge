# pyright: strict
"""Lecture de CSV en lignes de dictionnaires, sans logique métier.

`parse_csv` enveloppe le module standard `csv` : il lit un texte CSV et renvoie
une ligne par enregistrement, sous forme de dictionnaire en-tête -> valeur. La
validation et l'insertion ne sont pas ici (voir `engine.py`).
"""
from __future__ import annotations

import csv
import io

from forge_mvc_import_export.errors import CsvImportError


def parse_csv(text: str, *, delimiter: str = ",") -> list[dict[str, str]]:
    """Lit `text` (contenu CSV) et renvoie une liste de lignes en dictionnaire.

    La première ligne fournit les en-têtes (clés). Chaque ligne de données
    devient un `dict` en-tête -> valeur (les valeurs sont des chaînes). Lève
    :class:`CsvImportError` si le CSV n'a pas d'en-tête ou contient un en-tête
    vide ou dupliqué.
    """
    if not text.strip():
        raise CsvImportError("Le contenu CSV est vide.")

    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        raise CsvImportError("Le contenu CSV est vide.")

    header = [cell.strip() for cell in rows[0]]
    if any(not name for name in header):
        raise CsvImportError("L'en-tête CSV contient une colonne sans nom.")
    if len(set(header)) != len(header):
        raise CsvImportError("L'en-tête CSV contient des colonnes en double.")

    records: list[dict[str, str]] = []
    for cells in rows[1:]:
        if not any(cell.strip() for cell in cells):
            continue  # ligne entièrement vide ignorée
        record = {header[i]: (cells[i] if i < len(cells) else "") for i in range(len(header))}
        records.append(record)
    return records
